// @ts-nocheck
document.addEventListener("DOMContentLoaded", function() {
  const form = document.getElementById("uploadForm");
  const fileInput = document.getElementById("fileInput");
  const progressBar = document.getElementById("progress");
  const statusDiv = document.getElementById("status");
  const outputContainer = document.getElementById("outputContainer");
  const outputPath = document.getElementById("outputPath");
  const openButton = document.getElementById("openButton");

  form.addEventListener("submit", async function(e) {
    e.preventDefault();

    const files = fileInput.files;
    if (!files || files.length === 0) {
      alert("⚠️ Please select at least one image or video!");
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files[]", files[i]);
    }

    // Reset UI
    progressBar.style.width = "0%";
    progressBar.innerText = "0%";
    statusDiv.innerText = "⏳ Uploading files...";
    outputContainer.style.display = "none";

    try {
      const response = await fetch("/upload", { method: "POST", body: formData });
      const data = await response.json();

      if (data.status !== "success") {
        alert("❌ Error: " + data.message);
        return;
      }

      const firstUrl = data.sr_urls[0];
      const filename_no_ext = firstUrl.split("/")[2];
      const outputFolder = data.output_path || "C:\\\\INDOWINGS_OUTPUT";

      statusDiv.innerText = "⚡ Processing started...";

      // Poll progress every 500ms
      const interval = setInterval(async function() {
        const res = await fetch(`/progress/${filename_no_ext}`);
        const progressData = await res.json();
        const p = progressData.progress || 0;

        progressBar.style.width = p + "%";
        progressBar.innerText = p + "%";

        // Color animation (red → yellow → green)
        if (p < 50) {
          progressBar.style.background = "linear-gradient(90deg, #ff4b2b, #ff416c)";
        } else if (p < 90) {
          progressBar.style.background = "linear-gradient(90deg, #ffb347, #ffcc33)";
        } else {
          progressBar.style.background = "linear-gradient(90deg, #00b09b, #96c93d)";
        }

        if (p >= 100) {
          clearInterval(interval);
          statusDiv.innerText = "✅ Processing Complete!";
          outputPath.innerHTML = `📁 Output saved to: <b>${outputFolder}</b>`;
          outputContainer.style.display = "block";

          openButton.onclick = function() {
            fetch("/open-output-folder", { method: "GET" });
          };
        }
      }, 500);

    } catch (err) {
      console.error(err);
      alert("❌ Something went wrong during upload!");
    }
  });
});
