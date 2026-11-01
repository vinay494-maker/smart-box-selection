/**
 * BoxAI 3D Packing Visualizer
 * Uses Three.js with OrbitControls to render interactive 3D box packing models.
 * Includes isometric 2.5D Canvas fallback.
 */

class Box3DVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.itemMeshes = [];
        this.boxWireframe = null;
        this.isThreeLoaded = typeof THREE !== 'undefined';
        this.currentData = null;

        if (this.container && this.isThreeLoaded) {
            this.initThree();
        }
    }

    initThree() {
        // Setup Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf8fafc); // slate-50

        // Setup Camera
        const width = this.container.clientWidth || 500;
        const height = this.container.clientHeight || 400;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
        this.camera.position.set(60, 50, 70);

        // Setup Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);

        // Controls
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
        }

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
        this.scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.85);
        dirLight.position.set(50, 80, 50);
        dirLight.castShadow = true;
        this.scene.add(dirLight);

        const fillLight = new THREE.DirectionalLight(0x90caf9, 0.3);
        fillLight.position.set(-50, -20, -50);
        this.scene.add(fillLight);

        // Ground Grid
        const grid = new THREE.GridHelper(100, 20, 0x94a3b8, 0xe2e8f0);
        grid.position.y = -0.05;
        this.scene.add(grid);

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());

        // Animation Loop
        const animate = () => {
            requestAnimationFrame(animate);
            if (this.controls) this.controls.update();
            this.renderer.render(this.scene, this.camera);
        };
        animate();
    }

    onWindowResize() {
        if (!this.container || !this.renderer || !this.camera) return;
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    renderBoxPlan(boxData) {
        this.currentData = boxData;
        if (!this.isThreeLoaded) {
            this.renderCanvasFallback(boxData);
            return;
        }

        // Clear existing items and wireframe
        this.itemMeshes.forEach(mesh => this.scene.remove(mesh));
        this.itemMeshes = [];
        if (this.boxWireframe) {
            this.scene.remove(this.boxWireframe);
            this.boxWireframe = null;
        }

        const dims = boxData.dimensions;
        const bx = dims.length;
        const by = dims.height; // In Three.js, Y is UP! So box height -> Y
        const bz = dims.width;  // In Three.js, Z is depth! So box width -> Z

        // 1. Render Box Container Outline
        const boxGeometry = new THREE.BoxGeometry(bx, by, bz);
        
        // Translucent faces
        const boxMaterial = new THREE.MeshLambertMaterial({
            color: 0x94a3b8,
            transparent: true,
            opacity: 0.15,
            side: THREE.BackSide
        });
        const boxMesh = new THREE.Mesh(boxGeometry, boxMaterial);
        
        // Edges wireframe
        const edges = new THREE.EdgesGeometry(boxGeometry);
        const lineMaterial = new THREE.LineBasicMaterial({ color: 0x334155, linewidth: 2 });
        const wireframe = new THREE.LineSegments(edges, lineMaterial);
        boxMesh.add(wireframe);

        // Position box centered in ThreeJS coordinates (so center of box is at bx/2, by/2, bz/2 offset)
        boxMesh.position.set(bx / 2, by / 2, bz / 2);
        this.scene.add(boxMesh);
        this.boxWireframe = boxMesh;

        // 2. Render Placed Items
        const colorPalette = [
            0x3b82f6, // Blue
            0x10b981, // Emerald
            0xf59e0b, // Amber
            0x8b5cf6, // Violet
            0xec4899, // Pink
            0x06b6d4, // Cyan
            0xf97316, // Orange
            0x14b8a6, // Teal
        ];

        (boxData.placements || []).forEach((p, idx) => {
            const ix = p.oriented_dimensions.length;
            const iy = p.oriented_dimensions.height; // Z in warehouse -> Y in 3D scene
            const iz = p.oriented_dimensions.width;  // Y in warehouse -> Z in 3D scene

            const px = p.coordinates.x + ix / 2;
            const py = p.coordinates.z + iy / 2; // Bottom-up
            const pz = p.coordinates.y + iz / 2;

            const itemGeo = new THREE.BoxGeometry(ix - 0.1, iy - 0.1, iz - 0.1);
            
            const color = p.is_fragile ? 0xef4444 : colorPalette[idx % colorPalette.length];
            const itemMat = new THREE.MeshStandardMaterial({
                color: color,
                roughness: 0.3,
                metalness: 0.1,
                transparent: true,
                opacity: 0.88,
            });

            const mesh = new THREE.Mesh(itemGeo, itemMat);
            mesh.position.set(px, py, pz);

            // Item black outline
            const itemEdges = new THREE.EdgesGeometry(itemGeo);
            const itemLineMat = new THREE.LineBasicMaterial({
                color: p.is_fragile ? 0x991b1b : 0x1e293b,
                linewidth: 1.5
            });
            const itemWire = new THREE.LineSegments(itemEdges, itemLineMat);
            mesh.add(itemWire);

            // Metadata for tooltips
            mesh.userData = {
                step: p.step,
                name: p.name,
                sku: p.sku,
                dimensions: `${p.oriented_dimensions.length}×${p.oriented_dimensions.width}×${p.oriented_dimensions.height} cm`,
                weight: `${p.weight_kg} kg`,
                isFragile: p.is_fragile
            };

            this.scene.add(mesh);
            this.itemMeshes.push(mesh);
        });

        // Reposition camera to frame the box
        const maxDim = Math.max(bx, by, bz);
        this.camera.position.set(maxDim * 1.8, maxDim * 1.6, maxDim * 2.0);
        if (this.controls) {
            this.controls.target.set(bx / 2, by / 3, bz / 2);
            this.controls.update();
        }
    }

    renderCanvasFallback(boxData) {
        if (!this.container) return;
        this.container.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full p-6 text-center bg-slate-100 rounded-xl">
                <i class="fa-solid fa-cube text-5xl text-blue-500 mb-3 animate-bounce"></i>
                <h4 class="font-bold text-slate-800 text-lg">${boxData.box_name}</h4>
                <p class="text-sm text-slate-500 mt-1">${boxData.dimensions.length} × ${boxData.dimensions.width} × ${boxData.dimensions.height} cm</p>
                <div class="mt-4 p-3 bg-white rounded-lg border border-slate-200 text-xs font-mono text-left w-full max-w-sm">
                    <div class="font-bold text-slate-700 mb-1 border-b pb-1">3D Placement Matrix:</div>
                    ${(boxData.placements || []).map(p => `
                        <div class="py-0.5 flex justify-between">
                            <span class="font-medium text-blue-600">Step ${p.step}: ${p.name}</span>
                            <span class="text-slate-500">(${p.coordinates.x}, ${p.coordinates.y}, ${p.coordinates.z})</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    resetView() {
        if (!this.currentData || !this.camera) return;
        const dims = this.currentData.dimensions;
        const maxDim = Math.max(dims.length, dims.height, dims.width);
        this.camera.position.set(maxDim * 1.8, maxDim * 1.6, maxDim * 2.0);
        if (this.controls) {
            this.controls.target.set(dims.length / 2, dims.height / 3, dims.width / 2);
            this.controls.update();
        }
    }

    setTopView() {
        if (!this.currentData || !this.camera) return;
        const dims = this.currentData.dimensions;
        const maxDim = Math.max(dims.length, dims.width);
        this.camera.position.set(dims.length / 2, maxDim * 2.5, dims.width / 2);
        if (this.controls) {
            this.controls.target.set(dims.length / 2, 0, dims.width / 2);
            this.controls.update();
        }
    }
}

window.Box3DVisualizer = Box3DVisualizer;
