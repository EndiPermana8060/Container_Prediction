document.addEventListener("DOMContentLoaded", function () {
  const inputForm = document.getElementById("input-form");
  const fileUploadForm = document.getElementById("file-upload-form");
  const predictionOutput = document.getElementById("prediction-output");
  const processPredictionBtn = document.getElementById(
    "process-prediction-btn"
  );
  const loadingSpinner = document.getElementById("loading-spinner");
  const successMessage = document.getElementById("success-message");
  const showFormBtn = document.getElementById("show-form-btn");
  const predictionTable = document.getElementById("predictionsTable"); // Tambahkan ID tabel

  // Initially hide the input form, prediction output, and prediction table
  inputForm.style.display = "none";
  predictionOutput.style.display = "none";
  predictionTable.style.display = "none"; // Sembunyikan tabel

  // Add event listener to the button for showing the form
  showFormBtn.addEventListener("click", function () {
    if (inputForm.style.display === "none") {
      inputForm.style.display = "block";
      predictionOutput.style.display = "block";
      showFormBtn.textContent = "Hide Form";
    } else {
      inputForm.style.display = "none";
      predictionOutput.style.display = "none";
      showFormBtn.textContent = "Predict per Customer";

      // Clear form input fields
      inputForm.reset();
    }
  });

  processPredictionBtn.addEventListener("click", function () {
    // Get the file input element (if necessary)
    const fileInput = document.getElementById("file-upload");

    // Check if the table is visible
    const isTableVisible = predictionTable.style.display === "block";

    if (isTableVisible) {
      // Hide the table and textarea
      predictionTable.style.display = "none";
      predictionOutput.style.display = "none"; // Hide textarea as well
      return; // Exit function if the table is already visible
    }

    // Show loading spinner
    loadingSpinner.style.display = "block";

    // Send the POST request to the server
    fetch("/process-all-predictions", {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => {
        // Hide loading spinner
        loadingSpinner.style.display = "none";

        // Clear previous results
        predictionOutput.value = "";
        const tableBody = document.querySelector("#predictionsTable tbody");
        tableBody.innerHTML = "";

        // Check for errors
        if (data.error) {
          alert(data.error);
          return;
        }

        // Display predictions in the table and textarea
        const predictions = data.predictions;

        // Create table headers if not exist
        const tableHead = document.querySelector("#predictionsTable thead");
        if (!tableHead.hasChildNodes()) {
          const headerRow = document.createElement("tr");
          const headers = [
            "masked_name",
            "containertype",
            "comm_grade_ro",
            "qty_ro",
            "Prediction",
          ];
          headers.forEach((header) => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
          });
          tableHead.appendChild(headerRow);
        }

        predictions.forEach((entry) => {
          // Add to table
          const tr = document.createElement("tr");

          // Add specific input data to table columns
          const columns = [
            "masked_name",
            "containertype",
            "comm_grade_ro",
            "qty_ro",
          ];
          columns.forEach((col) => {
            const td = document.createElement("td");
            td.textContent = entry.input_data[col] || ""; // use empty string if data is missing
            tr.appendChild(td);
          });

          // Add prediction result to the table
          const tdPrediction = document.createElement("td");
          tdPrediction.textContent = entry.prediction;
          tr.appendChild(tdPrediction);
          tableBody.appendChild(tr);

          // Add to textarea
          predictionOutput.value += `${columns
            .map((col) => entry.input_data[col] || "")
            .join(", ")}, ${entry.prediction}\n`;
        });

        // Show the table and textarea
        predictionTable.style.display = "block";
        predictionOutput.style.display = "block"; // Ensure textarea is visible
      })
      .catch((error) => {
        // Hide loading spinner
        loadingSpinner.style.display = "none";
        alert("An error occurred while processing predictions.");
        console.error("Error:", error);
      });
  });

  inputForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const formData = new FormData(inputForm);

    fetch("/process-user_input", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.prediction) {
          let outputMessage = `Prediction: ${data.prediction}`;

          // Cek jika ada pesan tambahan dari server
          if (data.message) {
            outputMessage += `\n${data.message}`;
          }

          predictionOutput.value = outputMessage;
        } else if (data.error) {
          predictionOutput.value = `Error: ${data.error}`;
        }
      })
      .catch((error) => {
        predictionOutput.value = `An error occurred: ${error.message}`;
      });
  });

  // Ketika file diunggah dan proses upload selesai
  fileUploadForm.addEventListener("submit", function (event) {
    event.preventDefault();

    loadingSpinner.style.display = "inline-block";
    successMessage.style.display = "none";

    const formData = new FormData(fileUploadForm);

    fetch("/upload-excel", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        loadingSpinner.style.display = "none";
        successMessage.style.display = "block";

        if (data.user_id) {
          // Simpan user_id ke hidden input atau variabel global
          document.getElementById("user_id").value = data.user_id;
        }
      })
      .catch((error) => {
        loadingSpinner.style.display = "none";
        console.log(error);
      });
  });
});
