from flask import Flask, request, jsonify, render_template, session
import pickle
import pandas as pd
import numpy as np
import os
import constant
import uuid
from utils import Processor

app = Flask(__name__)
# Set a unique and secret key for sessions
app.secret_key = os.urandom(24)  # You can replace this with a hardcoded key if preferred
processer = Processor()
columns_for_processing = constant.for_processing

# Load the scaler and model from pickle files
with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

with open('new_cont_pred.pkl', 'rb') as f:
    model = pickle.load(f)

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Cek apakah 'user_id' sudah ada di session
    if 'user_id' not in session:
        # Jika tidak ada, buat UUID baru dan simpan di session
        session['user_id'] = str(uuid.uuid4())

    # Render template dengan UUID jika perlu
    return render_template('index.html', user_id=session['user_id'])


@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    # Ambil UUID dari session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is not set. Please generate UUID first."})

    # Ambil file dari request
    file = request.files['file']
    directory = 'user_excel'

    # Pastikan direktori untuk menyimpan file ada
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Simpan file
    file_path = os.path.join(directory, file.filename)
    file.save(file_path)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File did not save correctly."})

    # Coba baca file Excel
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        return jsonify({"error": f"Failed to read Excel file. Error: {str(e)}"})

    # Proses data dan simpan ke database dengan user_id dari session
    try:
        processer.save_to_db(df, user_id)
    except Exception as e:
        return jsonify({"error": str(e)})

    return jsonify({"message": "File uploaded and processed successfully", "user_id": user_id})



@app.route('/process-user_input', methods=['POST'])
def process_input():
    processor = Processor()
    try:
        user_id = request.form.get('user_id')

        input_data = {
            'containertype': int(request.form.get('containertype')),
            'masked_name': request.form.get('masked_name'),
            'comm_grade_ro': request.form.get('comm_grade_ro'),
            'qty_ro': int(request.form.get('qty_ro')),
            'user_id': user_id
        }
        print(input_data)
        # Convert input data to DataFrame
        data_raw = processor.get_feature_values(user_id=input_data['user_id'],
                                                containertype=input_data['containertype'],
                                                masked_name=input_data['masked_name'],
                                                comm_grade_ro=input_data['comm_grade_ro'])
        print(data_raw)
        if data_raw:
            new_key = 'qty_ro'
            value = input_data['qty_ro']

            new_data = {new_key:value, **data_raw}
        # Convert dict_result to a pandas DataFrame
            df_input = pd.DataFrame([new_data])
        # Now df_input is ready to be used in further processing (e.g., scaling, model prediction)
            print(df_input)
        else:
            return jsonify({'error': 'Data Not Found!'})

        # One-hot encode the input data
        df_encoded_input = pd.get_dummies(df_input, columns=['masked_name', 'containertype', 'comm_grade_ro', 'pod', 'customer_segmentation', 'vesselid'], dtype=int)
        
        # Align the columns to the model's expected features
        df_encoded_input_final = df_encoded_input.reindex(columns=columns_for_processing, fill_value=0)

        # Concatenate with the numerical data
        categorical_array = df_encoded_input_final.values

        # Scale the data
        df_scaled = scaler.transform(categorical_array)

        # Make predictions
        predictions = model.predict(df_scaled)
        rounded_predictions = round(predictions[0])
        print(predictions[0])
        print(rounded_predictions)
        # Compare rounded_predictions with qty_ro
        if rounded_predictions < input_data['qty_ro']:
            message = f"Request Order yang diapprove hanya {rounded_predictions} Container, Jika ingin Request Lebih banyak silahkan Approve manual."
        else:
            message = "The prediction was successful."

        return jsonify({'prediction': rounded_predictions, 'message': message})

    except:
        return jsonify({'error': 'Data Not Found!'})

@app.route('/process-all-predictions', methods=['POST'])
def process_all_predictions():
    processor = Processor()
    try:
        # Ambil user_id dari session
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({'error': 'User ID not found in session'})

        # Menggunakan fungsi get_all_feature_values untuk mengambil semua data dari database berdasarkan user_id
        all_data = processor.get_all_feature_values(user_id=user_id)
        print(all_data)
        if all_data is None:
            return jsonify({'error': 'Data not found!'})

        # List to store predictions
        predictions = []

        for data in all_data:
            # Prepare the input data for prediction
            input_data = {
                'qty_ro': data['qty_ro'],
                'masked_name': data['masked_name'],
                'containertype': data['containertype'],
                'comm_grade_ro': data['comm_grade_ro'],
                'pod': data['pod'],
                'customer_segmentation': data['customer_segmentation'],
                'vesselid': data['vesselid']
            }

            # Transform the input data using the scaler
            input_values = [[
                input_data['qty_ro'],
                input_data['masked_name'],
                input_data['containertype'],
                input_data['comm_grade_ro'],
                input_data['pod'],
                input_data['customer_segmentation'],
                input_data['vesselid']
            ]]

            df_input = pd.DataFrame(input_values, columns=['qty_ro', 'masked_name', 'containertype', 'comm_grade_ro', 'pod', 'customer_segmentation', 'vesselid'])

            # One-hot encode the input data
            df_encoded_input = pd.get_dummies(df_input, columns=['masked_name', 'containertype', 'comm_grade_ro', 'pod', 'customer_segmentation', 'vesselid'], dtype=int)

            # Align the columns to the model's expected features
            df_encoded_input_final = df_encoded_input.reindex(columns=columns_for_processing, fill_value=0)

            # Convert to array
            categorical_array = df_encoded_input_final.values

            # Scale the data
            df_scaled = scaler.transform(categorical_array)

            # Make prediction
            prediction = model.predict(df_scaled)

            # Store the prediction along with the relevant input data
            predictions.append({
                'input_data': input_data,
                'prediction': round(prediction[0])  # Assuming it's a single value prediction
            })

        # Return the list of predictions as JSON
        return jsonify({'predictions': predictions})

    except Exception as e:
        # Return an error message in case of exception
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
""