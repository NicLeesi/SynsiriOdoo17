/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { Component, xml, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";  // ✅ Add this import

// ✅ Custom Dialog Component with MULTIPLE UPLOAD inside dialog
class ImageSelectorDialog extends Component {
    static template = xml`
        <Dialog>
            <t t-set-slot="header">
                <t t-esc="dialogTitle"/>
            </t>

            <!-- Upload Button Section -->
            <div class="d-flex justify-content-between align-items-center p-3 bg-light border-bottom">
                <div>
                    <h6 class="mb-0">
                        <i class="fa fa-images"/>
                        <t t-esc="galleryTitle"/>
                        (<t t-esc="state.images.length"/> / <t t-esc="maxImages"/>)
                    </h6>
                </div>
                <button class="btn btn-primary"
                        t-on-click="triggerUpload"
                        t-att-disabled="state.images.length >= maxImages">
                    <i class="fa fa-upload"/> <t t-esc="uploadButtonText"/>
                </button>
            </div>

            <div class="paste-hint" style="background: #e7f3ff; padding: 10px; margin: 10px 20px; border-radius: 5px; text-align: center; font-size: 0.9em; color: #0066cc;">
                <i class="fa fa-info-circle"/>
                <t t-esc="pasteHintText"/>
            </div>

            <div class="image-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; padding: 20px; max-height: 500px; overflow-y: auto;">
                <t t-if="state.loading">
                    <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                        <i class="fa fa-spinner fa-spin fa-3x"/>
                        <p t-esc="loadingText"/>
                    </div>
                </t>

                <t t-elif="state.uploading">
                    <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                        <i class="fa fa-spinner fa-spin fa-2x" style="color: #007bff;"/>
                        <p>
                            <t t-esc="uploadingText"/>
                            <t t-esc="state.uploadProgress"/>
                            <t t-esc="imagesText"/>
                        </p>
                    </div>
                </t>

                <t t-elif="state.images.length === 0">
                    <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #666;">
                        <i class="fa fa-image fa-3x" style="opacity: 0.3;"/>
                        <p t-esc="noImagesText"/>
                        <p style="font-size: 0.9em;" t-esc="uploadToStartText"/>
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
                                    <i class="fa fa-check-circle"/> <t t-esc="newBadgeText"/>
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

        // Bind methods
        this.handlePaste = this.handlePaste.bind(this);
        this.selectImage = this.selectImage.bind(this);
        this.triggerUpload = this.triggerUpload.bind(this);
        this.loadImages = this.loadImages.bind(this);
        this.uploadMultipleImages = this.uploadMultipleImages.bind(this);

        this.dialogTitle = _t("Choose Cover Image");
        this.galleryTitle = _t("Image Gallery");
        this.uploadButtonText = _t("Upload Images");
        this.pasteHintText = _t("Tip: Press Ctrl+V to paste an image from clipboard or click Upload Images to select multiple files");
        this.loadingText = _t("Loading images...");
        this.uploadingText = _t("Uploading");
        this.imagesText = _t("images...");
        this.noImagesText = _t("No images found for this task.");
        this.uploadToStartText = _t("Upload images to get started.");
        this.newBadgeText = _t("New");

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
            this.notification.add(
                "Failed to load images. Please try again.",
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }

    triggerUpload() {
        // Check limit
        if (this.state.images.length >= this.maxImages) {
            this.notification.add(
                `Maximum ${this.maxImages} images allowed per task.`,
                { type: "warning" }
            );
            return;
        }

        // Create hidden file input
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*";
        input.multiple = true;
        input.style.display = "none";
        document.body.appendChild(input);

        input.onchange = async () => {
            const files = Array.from(input.files);
            if (files.length === 0) return;

            // Check if adding these files would exceed limit
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
                this.notification.add(
                    `Failed to upload ${file.name}`,
                    { type: "danger" }
                );
            }
        }

        if (uploadedIds.length > 0) {
            this.notification.add(
                `Successfully uploaded ${uploadedIds.length} image(s)!`,
                { type: "success" }
            );

            // Reload images
            await this.loadImages();

            // Mark newly uploaded images
            uploadedIds.forEach(id => {
                const newImage = this.state.images.find(img => img.id === id);
                if (newImage) {
                    newImage.isNew = true;
                }
            });
        }

        this.state.uploading = false;
    }

    async handlePaste(event) {
        if (!this.state) return;

        if (this.state.images.length >= this.maxImages) {
            event.preventDefault();
            this.notification.add(
                `Maximum ${this.maxImages} images allowed per task. Please delete some images first.`,
                { type: "warning" }
            );
            return;
        }

        if (this.state.uploading) {
            event.preventDefault();
            this.notification.add(
                "Please wait, still uploading...",
                { type: "warning" }
            );
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

                        const attachmentId = attachmentIds[0];

                        this.notification.add(
                            `Image pasted and uploaded successfully! (${this.state.images.length + 1}/${this.maxImages})`,
                            { type: "success" }
                        );

                        await this.loadImages();

                        const newImage = this.state.images.find(img => img.id === attachmentId);
                        if (newImage) {
                            newImage.isNew = true;
                        }

                    } catch (err) {
                        this.notification.add(
                            "Failed to upload pasted image.",
                            { type: "danger" }
                        );
                        console.error("Paste upload error:", err);
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

// ✅ Simplified FormController - Multiple upload is now inside the dialog
patch(FormController.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialogService = useService("dialog");
        this.maxImages = 8;

        // Bind methods
        this.onClickSetCoverImage = this.onClickSetCoverImage.bind(this);
        this.onClickChooseExistingCover = this.onClickChooseExistingCover.bind(this);
    },

    // Single cover image upload
    async onClickSetCoverImage() {
        const record = this.model.root;
        const resModel = record.resModel;
        const resId = record.resId;

        const existingImageCount = await this.orm.searchCount(
            "ir.attachment",
            [
                ["res_model", "=", resModel],
                ["res_id", "=", resId],
                ["mimetype", "ilike", "image"],
            ]
        );

        if (existingImageCount >= this.maxImages) {
            this.notification.add(
                `Maximum ${this.maxImages} images allowed per task. Please delete some images first.`,
                { type: "warning" }
            );
            return;
        }

        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*";
        input.style.display = "none";
        document.body.appendChild(input);

        input.onchange = async () => {
            const file = input.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async (e) => {
                const base64 = e.target.result.split(",")[1];

                try {
                    const attachmentIds = await this.orm.create("ir.attachment", [{
                        name: file.name,
                        datas: base64,
                        res_model: resModel,
                        res_id: resId,
                        mimetype: file.type,
                    }]);
                    const attachmentId = attachmentIds[0];

                    await this.orm.write(resModel, [resId], {
                        displayed_image_id: attachmentId
                    });

                    this.notification.add(
                        `Cover image "${file.name}" uploaded successfully. (${existingImageCount + 1}/${this.maxImages})`,
                        { type: "success" }
                    );

                    await this.model.load();
                } catch (err) {
                    this.notification.add(
                        "Something went wrong while uploading the image.",
                        { type: "danger" }
                    );
                    console.error("Full error:", err);
                } finally {
                    input.remove();
                }
            };
            reader.readAsDataURL(file);
        };

        input.click();
    },

    // Choose from existing images - NOW WITH UPLOAD INSIDE
    async onClickChooseExistingCover() {
        const record = this.model.root;
        const resModel = record.resModel;
        const resId = record.resId;

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

                    await this.model.load();
                } catch (err) {
                    this.notification.add(
                        "Failed to update cover image.",
                        { type: "danger" }
                    );
                    console.error("Error setting cover:", err);
                }
            },
            close: async () => {
            console.log("Dialog closed, reloading view...");
            await this.action.doAction({
                    type: "ir.actions.client",
                    tag: "reload",
                })
            }
        });
    },
});

export { ImageSelectorDialog };

