/**
 * CS:GO 3D 시뮬레이션 - Three.js 기반
 */
class CombatSimulation {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        this.data = null;
        this.currentTick = 0;
        this.isPlaying = false;
        this.playSpeed = 1;
        this.animationFrame = null;
        
        this.playerObjects = new Map();
        this.playerTrails = new Map();
        this.eventMarkers = [];
        
        this.init();
    }

    async init() {
        // Three.js 초기화
        this.setupScene();
        this.setupControls();
        
        // 데이터 로드
        await this.loadData();
        
        // UI 이벤트 설정
        this.setupUI();
        
        // 애니메이션 시작
        this.animate();
    }

    setupScene() {
        const container = document.getElementById('canvas-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0e27);
        this.scene.fog = new THREE.Fog(0x0a0e27, 1000, 5000);

        // Camera
        this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 10000);
        this.camera.position.set(0, 500, 1000);
        this.camera.lookAt(0, 0, 0);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: document.getElementById('canvas'),
            antialias: true 
        });
        this.renderer.setSize(width, height);
        this.renderer.shadowMap.enabled = true;

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(500, 1000, 500);
        directionalLight.castShadow = true;
        this.scene.add(directionalLight);

        // Grid helper
        const gridHelper = new THREE.GridHelper(5000, 50, 0x2a2f4a, 0x1a1f3a);
        this.scene.add(gridHelper);

        // Axis helper
        const axesHelper = new THREE.AxesHelper(500);
        this.scene.add(axesHelper);

        // Resize handler
        window.addEventListener('resize', () => {
            const width = container.clientWidth;
            const height = container.clientHeight;
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        });
    }

    setupControls() {
        // OrbitControls 사용 (CDN에서 로드한 경우)
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.minDistance = 100;
            this.controls.maxDistance = 5000;
            this.controls.target.set(0, 0, 0);
        } else {
            // OrbitControls가 없으면 간단한 컨트롤 구현
            let isMouseDown = false;
            let mouseX = 0;
            let mouseY = 0;
            let cameraRotationX = 0;
            let cameraRotationY = 0;
            let cameraDistance = 1500;

            const canvas = document.getElementById('canvas');
            
            canvas.addEventListener('mousedown', (e) => {
                isMouseDown = true;
                mouseX = e.clientX;
                mouseY = e.clientY;
            });

            canvas.addEventListener('mousemove', (e) => {
                if (isMouseDown) {
                    const deltaX = e.clientX - mouseX;
                    const deltaY = e.clientY - mouseY;
                    
                    cameraRotationY += deltaX * 0.01;
                    cameraRotationX += deltaY * 0.01;
                    
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                }
            });

            canvas.addEventListener('mouseup', () => {
                isMouseDown = false;
            });

            canvas.addEventListener('wheel', (e) => {
                cameraDistance += e.deltaY * 5;
                cameraDistance = Math.max(100, Math.min(5000, cameraDistance));
            });

            this.updateCamera = () => {
                const x = cameraDistance * Math.sin(cameraRotationY) * Math.cos(cameraRotationX);
                const y = cameraDistance * Math.sin(cameraRotationX);
                const z = cameraDistance * Math.cos(cameraRotationY) * Math.cos(cameraRotationX);
                
                this.camera.position.set(x, y, z);
                this.camera.lookAt(0, 0, 0);
            };
        }
    }

    async loadData() {
        try {
            const response = await fetch('/api/data');
            this.data = await response.json();
            
            // UI 업데이트
            this.updateUI();
            
            // 초기 틱 렌더링
            this.renderTick(0);
        } catch (error) {
            console.error('Failed to load data:', error);
        }
    }

    updateUI() {
        if (!this.data) return;

        const metadata = this.data.metadata;
        document.getElementById('total-ticks').textContent = metadata.total_ticks;
        document.getElementById('total-events').textContent = metadata.total_events;
        
        const duration = metadata.time_range.max - metadata.time_range.min;
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        document.getElementById('duration').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        // 플레이어 목록
        const playerList = document.getElementById('player-list');
        playerList.innerHTML = '';
        metadata.players.forEach(player => {
            const item = document.createElement('div');
            item.className = 'player-item';
            item.textContent = player;
            playerList.appendChild(item);
        });

        // 이벤트 로그
        this.updateEventLog();
    }

    updateEventLog() {
        const eventLog = document.getElementById('event-log');
        eventLog.innerHTML = '';
        
        if (!this.data || !this.data.events) return;

        this.data.events.slice(0, 10).forEach(event => {
            const item = document.createElement('div');
            item.className = 'event-item kill';
            const time = this.formatTime(event.game_time);
            item.textContent = `${time} - ${event.attacker.name} killed ${event.victim.name}`;
            eventLog.appendChild(item);
        });
    }

    renderTick(tickIndex) {
        if (!this.data || !this.data.positions) return;

        const tickData = this.data.positions[tickIndex];
        if (!tickData) return;

        // 기존 플레이어 오브젝트 제거
        this.playerObjects.forEach(obj => {
            this.scene.remove(obj);
        });
        this.playerObjects.clear();

        // 플레이어 렌더링
        tickData.players.forEach(player => {
            const geometry = new THREE.SphereGeometry(15, 16, 16);
            const color = player.team === 'CT' ? 0x5b9bd5 : 0xff6b6b;
            const material = new THREE.MeshPhongMaterial({ 
                color: color,
                emissive: color,
                emissiveIntensity: 0.3
            });
            
            const sphere = new THREE.Mesh(geometry, material);
            sphere.position.set(player.position[0], player.position[2], player.position[1]);
            sphere.castShadow = true;
            sphere.receiveShadow = true;
            
            this.scene.add(sphere);
            this.playerObjects.set(player.name, sphere);

            // 플레이어 이름 라벨 (간단한 텍스트)
            const sprite = this.createLabel(player.name);
            sprite.position.set(
                player.position[0],
                player.position[2] + 30,
                player.position[1]
            );
            this.scene.add(sprite);

            // 트레일 추가
            this.updateTrail(player.name, player.position);
        });

        // 이벤트 마커 렌더링
        this.renderEvents(tickData.game_time);
    }

    createLabel(text) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 64;
        
        context.fillStyle = 'rgba(0, 0, 0, 0.7)';
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.fillStyle = '#ffffff';
        context.font = '24px Arial';
        context.textAlign = 'center';
        context.fillText(text, canvas.width / 2, canvas.height / 2 + 8);
        
        const texture = new THREE.CanvasTexture(canvas);
        const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
        const sprite = new THREE.Sprite(spriteMaterial);
        sprite.scale.set(100, 25, 1);
        
        return sprite;
    }

    updateTrail(playerName, position) {
        if (!this.playerTrails.has(playerName)) {
            const trailGeometry = new THREE.BufferGeometry();
            const trailMaterial = new THREE.LineBasicMaterial({ 
                color: 0x4a90e2,
                opacity: 0.5,
                transparent: true
            });
            const trail = new THREE.Line(trailGeometry, trailMaterial);
            this.scene.add(trail);
            this.playerTrails.set(playerName, {
                line: trail,
                points: []
            });
        }

        const trail = this.playerTrails.get(playerName);
        trail.points.push(new THREE.Vector3(position[0], position[2], position[1]));
        
        // 최대 50개 포인트만 유지
        if (trail.points.length > 50) {
            trail.points.shift();
        }

        trail.line.geometry.setFromPoints(trail.points);
    }

    renderEvents(gameTime) {
        // 기존 이벤트 마커 제거
        this.eventMarkers.forEach(marker => {
            this.scene.remove(marker);
        });
        this.eventMarkers = [];

        // 현재 시간 근처의 이벤트 표시
        if (!this.data || !this.data.events) return;

        this.data.events.forEach(event => {
            const timeDiff = Math.abs(event.game_time - gameTime);
            if (timeDiff < 2.0 && event.attacker.position[0] !== null) {
                // 킬 이벤트 마커
                const geometry = new THREE.ConeGeometry(20, 60, 8);
                const material = new THREE.MeshPhongMaterial({ 
                    color: 0xff0000,
                    emissive: 0xff0000,
                    emissiveIntensity: 0.5
                });
                const marker = new THREE.Mesh(geometry, material);
                marker.position.set(
                    event.attacker.position[0],
                    event.attacker.position[2] + 30,
                    event.attacker.position[1]
                );
                marker.rotation.x = -Math.PI / 2;
                this.scene.add(marker);
                this.eventMarkers.push(marker);

                // 공격자에서 피해자로 라인
                if (event.victim.position[0] !== null) {
                    const lineGeometry = new THREE.BufferGeometry().setFromPoints([
                        new THREE.Vector3(
                            event.attacker.position[0],
                            event.attacker.position[2],
                            event.attacker.position[1]
                        ),
                        new THREE.Vector3(
                            event.victim.position[0],
                            event.victim.position[2],
                            event.victim.position[1]
                        )
                    ]);
                    const lineMaterial = new THREE.LineBasicMaterial({ 
                        color: 0xff6b6b,
                        opacity: 0.7,
                        transparent: true
                    });
                    const line = new THREE.Line(lineGeometry, lineMaterial);
                    this.scene.add(line);
                    this.eventMarkers.push(line);
                }
            }
        });
    }

    setupUI() {
        const playBtn = document.getElementById('play-btn');
        const timeline = document.getElementById('timeline');
        const speedButtons = document.querySelectorAll('.speed-btn');

        playBtn.addEventListener('click', () => {
            this.togglePlay();
        });

        timeline.addEventListener('click', (e) => {
            const rect = timeline.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            this.seekTo(percent);
        });

        speedButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                speedButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.playSpeed = parseFloat(btn.dataset.speed);
            });
        });
    }

    togglePlay() {
        this.isPlaying = !this.isPlaying;
        const playBtn = document.getElementById('play-btn');
        playBtn.textContent = this.isPlaying ? '⏸' : '▶';
    }

    seekTo(percent) {
        if (!this.data) return;
        const maxTick = this.data.positions.length - 1;
        this.currentTick = Math.floor(percent * maxTick);
        this.renderTick(this.currentTick);
        this.updateTimeDisplay();
    }

    updateTimeDisplay() {
        if (!this.data) return;
        
        const metadata = this.data.metadata;
        const currentTickData = this.data.positions[this.currentTick];
        
        if (currentTickData) {
            const currentTime = currentTickData.game_time - metadata.time_range.min;
            const totalTime = metadata.time_range.max - metadata.time_range.min;
            
            document.getElementById('time-display').textContent = 
                `${this.formatTime(currentTime)} / ${this.formatTime(totalTime)}`;
            
            const progress = (this.currentTick / (this.data.positions.length - 1)) * 100;
            document.getElementById('timeline-progress').style.width = `${progress}%`;
        }
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    animate() {
        this.animationFrame = requestAnimationFrame(() => this.animate());

        // OrbitControls 업데이트
        if (this.controls) {
            this.controls.update();
        } else if (this.updateCamera) {
            this.updateCamera();
        }

        // 재생 중이면 틱 업데이트
        if (this.isPlaying && this.data) {
            const now = Date.now();
            if (!this.lastUpdateTime) {
                this.lastUpdateTime = now;
            }
            
            const delta = (now - this.lastUpdateTime);
            if (delta > (16 / this.playSpeed)) { // 재생 속도에 따라 조절
                this.currentTick += 1;
                if (this.currentTick >= this.data.positions.length) {
                    this.currentTick = this.data.positions.length - 1;
                    this.isPlaying = false;
                    document.getElementById('play-btn').textContent = '▶';
                } else {
                    this.renderTick(this.currentTick);
                    this.updateTimeDisplay();
                }
                this.lastUpdateTime = now;
            }
        }

        this.renderer.render(this.scene, this.camera);
    }
}

// 초기화
window.addEventListener('DOMContentLoaded', () => {
    new CombatSimulation();
});

