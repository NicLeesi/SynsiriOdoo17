/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillUnmount, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// ✅ Full-screen Image Viewer Component (no dialog)
class ImagePreviewOverlay extends Component {
    static template = "project_gamification.ImagePreviewOverlay";
    static props = {
        close: Function,
        images: Array,
        currentIndex: Number,
    };

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            currentIndex: this.props.currentIndex,
            rotation: 0,
            zoom: 1,
        });

        // Bind keyboard events
        this.handleKeydown = this.handleKeydown.bind(this);
        document.addEventListener('keydown', this.handleKeydown);

        onWillUnmount(() => {
            document.removeEventListener('keydown', this.handleKeydown);
        });
    }

    get currentImage() {
        return this.props.images[this.state.currentIndex];
    }

    get hasPrevious() {
        return this.state.currentIndex > 0;
    }

    get hasNext() {
        return this.state.currentIndex < this.props.images.length - 1;
    }

    get imageStyle() {
        return `transform: rotate(${this.state.rotation}deg) scale(${this.state.zoom}); transition: transform 0.3s;`;
    }

    handleKeydown(event) {
        if (["ArrowLeft", "ArrowRight", "Escape"].includes(event.key)) {
        event.preventDefault();
        event.stopPropagation();
        }
        if (event.key === 'ArrowLeft' && this.hasPrevious) {
            this.previous();
        } else if (event.key === 'ArrowRight' && this.hasNext) {
            this.next();
        } else if (event.key === 'Escape') {
            this.props.close();
        }
    }

    previous() {
        if (this.hasPrevious) {
            this.state.currentIndex--;
            this.resetTransform();
        }
    }

    next() {
        if (this.hasNext) {
            this.state.currentIndex++;
            this.resetTransform();
        }
    }

    resetTransform() {
        this.state.rotation = 0;
        this.state.zoom = 1;
    }

    rotateLeft() {
        this.state.rotation -= 90;
    }

    rotateRight() {
        this.state.rotation += 90;
    }

    zoomIn() {
        if (this.state.zoom < 3) {
            this.state.zoom += 0.25;
        }
    }

    zoomOut() {
        if (this.state.zoom > 0.5) {
            this.state.zoom -= 0.25;
        }
    }

    resetZoom() {
        this.state.zoom = 1;
    }

    async downloadImage() {
        try {
            const imageUrl = `/web/image/${this.currentImage.id}`;
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = this.currentImage.name;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.notification.add(
                `Downloading ${this.currentImage.name}`,
                { type: "success" }
            );
        } catch (error) {
            this.notification.add(
                "Failed to download image",
                { type: "danger" }
            );
        }
    }

    printImage() {
        const imageUrl = `/web/image/${this.currentImage.id}`;
        const printWindow = window.open(imageUrl, '_blank');
        printWindow.onload = function() {
            printWindow.print();
        };
    }

    onBackdropClick() {
        this.props.close();
    }
}

// ✅ Main Image Gallery Widget
export class ImageGalleryWidget extends Component {
    static template = "project_gamification.ImageGalleryWidget";

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = useState({
            images: [],
            loading: true,
        });

        this.loadImages();
    }

    async loadImages() {
        const resId = this.props.record.resId;
        if (!resId) {
            this.state.loading = false;
            return;
        }

        try {
            const images = await this.orm.searchRead(
                "ir.attachment",
                [
                    ["res_model", "=", "project.task"],
                    ["res_id", "=", resId],
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

    openPreview(imageId) {
        const currentIndex = this.state.images.findIndex(img => img.id === imageId);

        this.dialog.add(ImagePreviewOverlay, {
            images: this.state.images,
            currentIndex: currentIndex,
        });
    }
}

registry.category("fields").add("image_gallery", {
    component: ImageGalleryWidget,
    supportedTypes: ["one2many"],
});