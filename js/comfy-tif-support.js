import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
	name: "a.unique.name.for.a.useless.extension",
	async setup() {
		function messageHandler(event) { alert(event.detail.message); }
        api.addEventListener("example.imageselector.textmessage", messageHandler);
	},
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeType.comfyClass=="Load Image (with tif support)") {
			const onConnectionsChange = nodeType.prototype.onConnectionsChange;
			nodeType.prototype.onConnectionsChange = function (side,slot,connect,link_info,output) {
				const r = onConnectionsChange?.apply(this, arguments);
				console.log("Someone changed my connection!");
				return r;
			};
		}
	},
	async getCustomWidgets(app) {
		console.log("Hello from widget");
		return {
					CUSTOM(node, inputName, inputData, app) {

						async function uploadFile(file, updateNode, pasted = false) {

							const img = new Image();
							img.onload = () => {
								node.imgs = [img];
								app.graph.setDirtyCanvas(true);
							};

							const response = api.fetchApi(`/tiff?filename=${file.name}&type=input`);

							response.then((response) => response.blob())
								.then((blob) => URL.createObjectURL(blob))
  								.then((url) => console.log((img.src = url)))
  								.catch((err) => console.error(err));


						}

						const fileInput = document.createElement("input");
						Object.assign(fileInput, {
							type: "file",
							accept: "image/tiff",
							style: "display: none",
							onchange: async () => {
								if (fileInput.files.length) {
									await uploadFile(fileInput.files[0], true);
								}
							},
						});
						document.body.append(fileInput);

						// Create the button widget for selecting the files
						let uploadWidget = node.addWidget("button", "choose file to upload", "image", () => {
							fileInput.click();
						});
						uploadWidget.serialize = false;

						return {
							widget : uploadWidget
						}
					}
				}
	}
});