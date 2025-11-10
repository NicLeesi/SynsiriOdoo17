/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProjectTaskKanbanRecord } from "@project/views/project_task_kanban/project_task_kanban_record";
import { useService } from "@web/core/utils/hooks";
import { Component, xml, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

class ImageSelectorDialog extends Component {
    static template = xml`
        <Dialog title="'Choose Cover Image'">
            <!-- Upload Button Section -->
            <div class="d-flex justify-content-between align-items-center p-3 bg-light border-bottom">
                <div>
                    <h6 class="mb-0">
                        <i class="fa fa-images"/> Image Gallery
                        (<t t-esc="state.images.length"/> / <t t-esc="maxImages"/>)
                    </h6>
                </div>
                <button class="btn btn-primary"
                        t-on-click="triggerUpload"
                        t-att-disabled="state.images.length >= maxImages">
                    <i class="fa fa-upload"/> Upload Images
                </button>
            </div>

            <div class="paste-hint" style="background: #e7f3ff; padding: 10px; margin: 10px 20px; border-radius: 5px; text-align: center; font-size: 0.9em; color: #0066cc;">
                <i class="fa fa-info-circle"/> Tip: Press <strong>Ctrl+V</strong> to paste an image from clipboard or click Upload Images to select multiple files
            </div>

            <div class="image-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; padding: 20px; max-height: 500px; overflow-y: auto;">
                <t t-if="state.loading">
                    <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                        <i class="fa fa-spinner fa-spin fa-3x"/>
                        <p>Loading images...</p>
                    </div>
                </t>

                <t t-elif="state.uploading">
                    <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                        <i class="fa fa-spinner fa-spin fa-2x" style="color: #007bff;"/>
                        <p>Uploading <t t-esc="state.uploadProgress"/> images...</p>
                    </div>
                </t>

                <t t-elif="state.images.length === 0">
                    <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #666;">
                        <i class="fa fa-image fa-3x" style="opacity: 0.3;"/>
                        <p>No images found for this task.</p>
                        <p style="font-size: 0.9em;">Upload images to get started.</p>
                    </div>
                </t>

                <t t-else="">
                    <div t-foreach="state.images" t-as="image" t-key="image.id"
                         class="image-item"
                         t-att-data-image-id="image.id"
                         t-on-click="selectImage"
                         style="cursor: pointer; border: 2px solid transparent; border-radius: 8px; overflow: hidden; transition: all 0.2s;">

                        <img t-att-src="'/web/image/' + image.id"
                             t-att-alt="image.name"
                             style="width: 100%; height: 150px; object-fit: cover;"/>

                        <div style="padding: 8px; background: #f8f9fa; font-size: 0.85em; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            <t t-if="image.isNew">
                                <span style="color: #28a745; font-weight: bold;">
                                    <i class="fa fa-check-circle"/> New
                                </span>
                                <br/>
                            </t>
                            <t t-esc="image.name"/>
                        </div>
                    </div>
                </t>
            </div>
        </Dialog>
    `;

    static components = { Dialog };
    static props = {
        close: Function,
        resModel: String,
        resId: Number,
        onSelect: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.maxImages = 8;
        this.state = useState({
            images: [],
            loading: true,
            uploading: false,
            uploadProgress: 0,
        });

        this.handlePaste = this.handlePaste.bind(this);
        this.selectImage = this.selectImage.bind(this);
        this.triggerUpload = this.triggerUpload.bind(this);
        this.loadImages = this.loadImages.bind(this);
        this.uploadMultipleImages = this.uploadMultipleImages.bind(this);

        onMounted(() => {
            document.addEventListener('paste', this.handlePaste);
        });

        onWillUnmount(() => {
            document.removeEventListener('paste', this.handlePaste);
        });

        this.loadImages();
    }

    async loadImages() {
        try {
            const images = await this.orm.searchRead(
                "ir.attachment",
                [
                    ["res_model", "=", this.props.resModel],
                    ["res_id", "=", this.props.resId],
                    ["mimetype", "ilike", "image"],
                ],
                ["id", "name", "mimetype"],
                { order: "create_date desc" }
            );

            this.state.images = images;
        } catch (error) {
            console.error("Failed to load images:", error);
        } finally {
            this.state.loading = false;
        }
    }

    triggerUpload() {
        if (this.state.images.length >= this.maxImages) {
            this.notification.add(
                `Maximum ${this.maxImages} images allowed per task.`,
                { type: "warning" }
            );
            return;
        }

        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*";
        input.multiple = true;
        input.style.display = "none";
        document.body.appendChild(input);

        input.onchange = async () => {
            const files = Array.from(input.files);
            if (files.length === 0) return;

            const remainingSlots = this.maxImages - this.state.images.length;
            if (files.length > remainingSlots) {
                this.notification.add(
                    `You can only upload ${remainingSlots} more image(s). Maximum ${this.maxImages} images per task.`,
                    { type: "warning" }
                );
                input.remove();
                return;
            }

            await this.uploadMultipleImages(files);
            input.remove();
        };

        input.click();
    }

    async uploadMultipleImages(files) {
        this.state.uploading = true;
        this.state.uploadProgress = 0;
        const uploadedIds = [];

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            this.state.uploadProgress = `${i + 1}/${files.length}`;

            try {
                const reader = new FileReader();
                const base64 = await new Promise((resolve, reject) => {
                    reader.onload = (e) => resolve(e.target.result.split(",")[1]);
                    reader.onerror = reject;
                    reader.readAsDataURL(file);
                });

                const attachmentIds = await this.orm.create("ir.attachment", [{
                    name: file.name,
                    datas: base64,
                    res_model: this.props.resModel,
                    res_id: this.props.resId,
                    mimetype: file.type,
                }]);

                uploadedIds.push(attachmentIds[0]);
            } catch (err) {
                console.error(`Failed to upload ${file.name}:`, err);
                this.notification.add(`Failed to upload ${file.name}`, { type: "danger" });
            }
        }

        if (uploadedIds.length > 0) {
            this.notification.add(
                `Successfully uploaded ${uploadedIds.length} image(s)!`,
                { type: "success" }
            );

            await this.loadImages();

            uploadedIds.forEach(id => {
                const newImage = this.state.images.find(img => img.id === id);
                if (newImage) newImage.isNew = true;
            });
        }

        this.state.uploading = false;
    }

    async handlePaste(event) {
        if (!this.state || this.state.images.length >= this.maxImages || this.state.uploading) {
            event.preventDefault();
            return;
        }

        const items = event.clipboardData?.items;
        if (!items) return;

        for (let i = 0; i < items.length; i++) {
            const item = items[i];

            if (item.type.indexOf('image') !== -1) {
                event.preventDefault();
                const blob = item.getAsFile();
                if (!blob) continue;

                const reader = new FileReader();
                reader.onload = async (e) => {
                    const base64 = e.target.result.split(",")[1];
                    this.state.uploading = true;

                    try {
                        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                        const filename = `pasted-image-${timestamp}.png`;

                        const attachmentIds = await this.orm.create("ir.attachment", [{
                            name: filename,
                            datas: base64,
                            res_model: this.props.resModel,
                            res_id: this.props.resId,
                            mimetype: blob.type || 'image/png',
                        }]);

                        this.notification.add(
                            `Image pasted successfully! (${this.state.images.length + 1}/${this.maxImages})`,
                            { type: "success" }
                        );

                        await this.loadImages();

                        const newImage = this.state.images.find(img => img.id === attachmentIds[0]);
                        if (newImage) newImage.isNew = true;
                    } catch (err) {
                        console.error("Paste upload error:", err);
                        this.notification.add("Failed to upload pasted image.", { type: "danger" });
                    } finally {
                        this.state.uploading = false;
                    }
                };
                reader.readAsDataURL(blob);
                break;
            }
        }
    }

    selectImage(ev) {
        const imageItem = ev.currentTarget;
        const imageId = parseInt(imageItem.dataset.imageId);

        if (imageId) {
            this.props.onSelect(imageId);
            this.props.close();
        }
    }
}

// ✅ Patch ProjectTaskKanbanRecord
patch(ProjectTaskKanbanRecord.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialogService = useService("dialog");
        this.maxImages = 8;

        // ✅ Attach click handlers after mount
        onMounted(() => {
            this.attachUploadButtonHandlers();
        });
    },

    // ✅ Attach handlers to buttons added via XML
    attachUploadButtonHandlers() {
        const root = this.rootRef?.el;
        if (!root) return;

        // Find all upload buttons with class from XML
        const uploadButtons = root.querySelectorAll('.o_kanban_upload_cover, .o_kanban_upload_cover_wrapper');

        console.log("Found", uploadButtons.length, "upload button(s) in kanban card");

        uploadButtons.forEach(button => {
            button.addEventListener('click', (ev) => {
                console.log("Upload button clicked, stopping propagation");
                ev.stopPropagation();
                ev.preventDefault();
                ev.stopImmediatePropagation();
                this.onCustomButtonClick(ev);
            }, true); // Use capture phase
        });
    },

    // ✅ Your custom button click handler
    async onCustomButtonClick(ev) {
        console.log("===== onCustomButtonClick called =====");

        const record = this.props.record;
        const resModel = record.resModel;
        const resId = record.resId;

        console.log("resModel:", resModel, "resId:", resId);

        if (!resId) {
            this.notification.add("Record not saved yet.", { type: "warning" });
            return;
        }

        // Check image limit
        try {
            const existingCount = await this.orm.searchCount("ir.attachment", [
                ["res_model", "=", resModel],
                ["res_id", "=", resId],
                ["mimetype", "ilike", "image"],
            ]);

            if (existingCount >= this.maxImages) {
                this.notification.add(
                    `Maximum ${this.maxImages} images allowed per task.`,
                    { type: "warning" }
                );
                return;
            }

            // Open dialog
            console.log("Opening ImageSelectorDialog...");
            this.dialogService.add(ImageSelectorDialog, {
                resModel: resModel,
                resId: resId,
                onSelect: async (imageId) => {
                    try {
                        await this.orm.write(resModel, [resId], {
                            displayed_image_id: imageId
                        });

                        this.notification.add(
                            "Cover image updated successfully!",
                            { type: "success" }
                        );

                        // Reload kanban
                        await this.props.record.model.root.load();
                    } catch (err) {
                        console.error("Error setting cover:", err);
                        this.notification.add(
                            "Failed to update cover image.",
                            { type: "danger" }
                        );
                    }
                }
            });
        } catch (error) {
            console.error("Error:", error);
            this.notification.add("Failed to open dialog.", { type: "danger" });
        }
    },
});

export { ImageSelectorDialog };