document.getElementById("upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("image").files[0];
  const task = document.getElementById("task").value;
  if (!file) return alert("Please upload an image!");

  const formData = new FormData();
  formData.append("image", file);

  const res = await fetch(`/${task}`, {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  if (data.image_base64) {
    document.getElementById("output-image").src = "data:image/jpeg;base64," + data.image_base64;
  }
  document.getElementById("output-text").textContent = JSON.stringify(data, null, 2);
});