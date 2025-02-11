import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
	name: "comfy-tif-support",
	async setup() {},

	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeType.comfyClass=="Load Image (with tif support)") {
			const onConnectionsChange = nodeType.prototype.onConnectionsChange;
			nodeType.prototype.onConnectionsChange = function (side,slot,connect,link_info,output) {
				const r = onConnectionsChange?.apply(this, arguments);
				return r;
			};
		}
	},

	async getCustomWidgets(app) {
		return {
					CUSTOM(node, inputName, inputData, app) {
						const imageWidget = node.addWidget('combo', "image", [], () => {}, {
							values:  inputData[1].files
						});

						async function showImage(file) {

								const img = new Image();
								img.onload = () => {
									node.imgs = [img];
									app.graph.setDirtyCanvas(true);
								};

								const response = api.fetchApi(`/tiff?filename=${file}&type=input`);

								response.then((response) => response.blob())
									.then((blob) => URL.createObjectURL(blob))
									.then((url) => console.log((img.src = url)))
									.catch((err) => console.error(err));

							node.setSizeForImage?.()
						}

						var default_value = imageWidget.value
						Object.defineProperty(imageWidget, "value", {
							set : function(value) {
								this._real_value = value;
							},

							get : function() {
								let value = "";
								if (this._real_value) {
									value = this._real_value;
								} else {
									return default_value;
								}

								if (value.filename) {
									let real_value = value;
									value = "";
									if (real_value.subfolder) {
										value = real_value.subfolder + "/";
									}

									value += real_value.filename;

									if(real_value.type && real_value.type !== "input")
										value += ` [${real_value.type}]`;
								}
								return value;
							}
						});

						const cb = node.callback;
							imageWidget.callback = function () {
								showImage(imageWidget.value);
								if (cb) {
									return cb.apply(this, arguments);
								}
						};

						async function uploadFile(file, updateNode, pasted = false) {
							try {
								// Wrap file in formdata so it includes filename
								const body = new FormData();
								body.append("image", file);
								if (pasted) body.append("subfolder", "pasted");
								const resp = await api.fetchApi("/upload/image", {
									method: "POST",
									body,
								});

								if (resp.status === 200) {
									const data = await resp.json();
									// Add the file to the dropdown list and update the widget value
									let path = data.name;
									if (data.subfolder) path = data.subfolder + "/" + path;

									if (!imageWidget.options.values.includes(path)) {
										imageWidget.options.values.push(path);
									}

									if (updateNode) {
										showImage(path);
										imageWidget.value = path;
									}
								} else {
									alert(resp.status + " - " + resp.statusText);
								}
							} catch (error) {
								alert(error);
							}
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