const form = document.getElementById('uploadForm');
const statusDiv = document.getElementById('status');
const progressBar = document.getElementById('progress');

form.addEventListener('submit', async e => {
    e.preventDefault();
    const files = document.getElementById('fileInput').files;
    if(files.length === 0) return alert("Select at least one video or image!");

    const formData = new FormData();
    for(let i = 0; i < files.length; i++) formData.append('files[]', files[i]);

    // Reset UI
    progressBar.style.width = "0%";
    progressBar.innerText = "0%";
    statusDiv.innerText = "⏳ Uploading...";

    try {
        const response = await fetch('/upload',{method:'POST',body:formData});
        const data = await response.json();

        if(data.status !== 'success'){
            alert("❌ Error: " + data.message);
            return;
        }

        const firstUrl = data.sr_urls[0];
        const filename_no_ext = firstUrl.split("/")[2];

        statusDiv.innerText = "⚡ Processing...";

        // Poll progress
        const interval = setInterval(async () => {
            const res = await fetch(`/progress/${filename_no_ext}`);
            const p = await res.json();
            progressBar.style.width = p.progress + "%";
            progressBar.innerText = p.progress + "%";

            if(p.progress >= 100){
                clearInterval(interval);
                statusDiv.innerText = "✅ Processing Complete!";
            }
        }, 200);

    } catch(err){
        console.error(err);
        alert("❌ Something went wrong!");
    }
});
