import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import BMOGPT, { BMOSettings } from 'src/main';

const execAsync = promisify(exec);

export interface PythonEnvironmentStatus {
    miniforgeInstalled: boolean;
    brainEnvironmentExists: boolean;
    brainPackageInstalled: boolean;
    brainServerRunning: boolean;
    pythonVersion?: string;
    condaVersion?: string;
    brainVersion?: string;
}

export interface InstallationProgress {
    step: string;
    progress: number;
    message: string;
    error?: string;
}

export class PythonEnvironmentManager {
    private plugin: BMOGPT;
    private settings: BMOSettings;
    private baseDir: string;
    private miniforgeDir: string;
    private brainEnvName = 'ghost-brain';

    constructor(plugin: BMOGPT, settings: BMOSettings) {
        this.plugin = plugin;
        this.settings = settings;
        this.baseDir = this.plugin.app.vault.adapter.getFullPath('.obsidian/plugins/bmo-chatbot');
        this.miniforgeDir = path.join(this.baseDir, 'miniforge');
    }

    /**
     * Get the current status of the Python environment
     */
    async getStatus(): Promise<PythonEnvironmentStatus> {
        const status: PythonEnvironmentStatus = {
            miniforgeInstalled: false,
            brainEnvironmentExists: false,
            brainPackageInstalled: false,
            brainServerRunning: false
        };

        try {
            // Check if miniforge is installed
            status.miniforgeInstalled = await this.checkMiniforgeInstalled();
            
            if (status.miniforgeInstalled) {
                // Check Python version
                status.pythonVersion = await this.getPythonVersion();
                
                // Check conda version
                status.condaVersion = await this.getCondaVersion();
                
                // Check if brain environment exists
                status.brainEnvironmentExists = await this.checkBrainEnvironmentExists();
                
                if (status.brainEnvironmentExists) {
                    // Check if brain package is installed
                    status.brainPackageInstalled = await this.checkBrainPackageInstalled();
                    
                    if (status.brainPackageInstalled) {
                        // Check brain version
                        status.brainVersion = await this.getBrainVersion();
                        
                        // Check if brain server is running
                        status.brainServerRunning = await this.checkBrainServerRunning();
                    }
                }
            }
        } catch (error) {
            console.error('Error checking Python environment status:', error);
        }

        return status;
    }

    /**
     * Install the complete Python environment (miniforge + brain)
     */
    async installEnvironment(
        onProgress?: (progress: InstallationProgress) => void
    ): Promise<boolean> {
        try {
            // Step 1: Install miniforge
            onProgress?.({
                step: 'miniforge',
                progress: 10,
                message: 'Installing Miniforge...'
            });

            if (!(await this.installMiniforge())) {
                throw new Error('Failed to install Miniforge');
            }

            // Step 2: Create brain environment
            onProgress?.({
                step: 'environment',
                progress: 30,
                message: 'Creating brain environment...'
            });

            if (!(await this.createBrainEnvironment())) {
                throw new Error('Failed to create brain environment');
            }

            // Step 3: Install brain package
            onProgress?.({
                step: 'brain',
                progress: 60,
                message: 'Installing brain package...'
            });

            if (!(await this.installBrainPackage())) {
                throw new Error('Failed to install brain package');
            }

            // Step 4: Verify installation
            onProgress?.({
                step: 'verify',
                progress: 90,
                message: 'Verifying installation...'
            });

            const status = await this.getStatus();
            if (!status.brainPackageInstalled) {
                throw new Error('Brain package installation verification failed');
            }

            onProgress?.({
                step: 'complete',
                progress: 100,
                message: 'Installation complete!'
            });

            return true;
        } catch (error) {
            onProgress?.({
                step: 'error',
                progress: 0,
                message: 'Installation failed',
                error: error instanceof Error ? error.message : String(error)
            });
            return false;
        }
    }

    /**
     * Start the brain server
     */
    async startBrainServer(): Promise<boolean> {
        try {
            const status = await this.getStatus();
            if (!status.brainPackageInstalled) {
                throw new Error('Brain package not installed. Please install the environment first.');
            }

            // Start brain server in background
            const brainDir = path.join(this.baseDir, 'brain');
            const command = `cd "${brainDir}" && conda run -n ${this.brainEnvName} python -m ghost_brain.server`;
            
            // Use platform-specific command
            const platformCommand = process.platform === 'win32' 
                ? `start /B ${command}`
                : `${command} > /dev/null 2>&1 &`;

            await execAsync(platformCommand);
            
            // Wait a moment for server to start
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Verify server is running
            return await this.checkBrainServerRunning();
        } catch (error) {
            console.error('Error starting brain server:', error);
            return false;
        }
    }

    /**
     * Stop the brain server
     */
    async stopBrainServer(): Promise<boolean> {
        try {
            // Find and kill brain server process
            const command = process.platform === 'win32'
                ? 'taskkill /F /IM python.exe /FI "WINDOWTITLE eq ghost_brain.server"'
                : 'pkill -f "ghost_brain.server"';

            await execAsync(command);
            return true;
        } catch (error) {
            console.error('Error stopping brain server:', error);
            return false;
        }
    }

    /**
     * Check if miniforge is installed
     */
    private async checkMiniforgeInstalled(): Promise<boolean> {
        try {
            const condaPath = path.join(this.miniforgeDir, 'bin', 'conda');
            await execAsync(`"${condaPath}" --version`);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Install miniforge
     */
    private async installMiniforge(): Promise<boolean> {
        try {
            // Create miniforge directory
            if (!fs.existsSync(this.miniforgeDir)) {
                fs.mkdirSync(this.miniforgeDir, { recursive: true });
            }

            // Download and install miniforge
            const platform = process.platform;
            const arch = process.arch === 'x64' ? 'x86_64' : 'aarch64';
            
            let installerUrl: string;
            let installerName: string;

            if (platform === 'win32') {
                installerName = `Miniforge3-Windows-${arch}.exe`;
                installerUrl = `https://github.com/conda-forge/miniforge/releases/latest/download/${installerName}`;
            } else if (platform === 'darwin') {
                installerName = `Miniforge3-MacOSX-${arch}.sh`;
                installerUrl = `https://github.com/conda-forge/miniforge/releases/latest/download/${installerName}`;
            } else {
                installerName = `Miniforge3-Linux-${arch}.sh`;
                installerUrl = `https://github.com/conda-forge/miniforge/releases/latest/download/${installerName}`;
            }

            const installerPath = path.join(this.miniforgeDir, installerName);

            // Download installer
            await this.downloadFile(installerUrl, installerPath);

            // Install miniforge
            if (platform === 'win32') {
                await execAsync(`"${installerPath}" /S /D="${this.miniforgeDir}"`);
            } else {
                await execAsync(`bash "${installerPath}" -b -p "${this.miniforgeDir}"`);
            }

            return true;
        } catch (error) {
            console.error('Error installing miniforge:', error);
            return false;
        }
    }

    /**
     * Create brain environment
     */
    private async createBrainEnvironment(): Promise<boolean> {
        try {
            const condaPath = path.join(this.miniforgeDir, 'bin', 'conda');
            await execAsync(`"${condaPath}" create -n ${this.brainEnvName} python=3.11 -y`);
            return true;
        } catch (error) {
            console.error('Error creating brain environment:', error);
            return false;
        }
    }

    /**
     * Install brain package
     */
    private async installBrainPackage(): Promise<boolean> {
        try {
            const condaPath = path.join(this.miniforgeDir, 'bin', 'conda');
            const brainDir = path.join(this.baseDir, 'brain');
            
            // Install dependencies
            await execAsync(`"${condaPath}" run -n ${this.brainEnvName} pip install -r "${path.join(brainDir, 'requirements.txt')}"`);
            
            // Install brain package in editable mode
            await execAsync(`"${condaPath}" run -n ${this.brainEnvName} pip install -e "${brainDir}"`);
            
            return true;
        } catch (error) {
            console.error('Error installing brain package:', error);
            return false;
        }
    }

    /**
     * Check if brain environment exists
     */
    private async checkBrainEnvironmentExists(): Promise<boolean> {
        try {
            const condaPath = path.join(this.miniforgeDir, 'bin', 'conda');
            await execAsync(`"${condaPath}" env list | grep ${this.brainEnvName}`);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Check if brain package is installed
     */
    private async checkBrainPackageInstalled(): Promise<boolean> {
        try {
            const condaPath = path.join(this.miniforgeDir, 'bin', 'conda');
            await execAsync(`"${condaPath}" run -n ${this.brainEnvName} python -c "import ghost_brain"`);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Check if brain server is running
     */
    private async checkBrainServerRunning(): Promise<boolean> {
        try {
            const response = await fetch('http://localhost:8000/health');
            return response.ok;
        } catch {
            return false;
        }
    }

    /**
     * Get Python version
     */
    private async getPythonVersion(): Promise<string> {
        try {
            const condaPath = path.join(this.miniforgeDir, 'bin', 'conda');
            const { stdout } = await execAsync(`"${condaPath}" run -n ${this.brainEnvName} python --version`);
            return stdout.trim();
        } catch {
            return 'Unknown';
        }
    }

    /**
     * Get conda version
     */
    private async getCondaVersion(): Promise<string> {
        try {
            const condaPath = path.join(this.miniforgeDir, 'bin', 'conda');
            const { stdout } = await execAsync(`"${condaPath}" --version`);
            return stdout.trim();
        } catch {
            return 'Unknown';
        }
    }

    /**
     * Get brain version
     */
    private async getBrainVersion(): Promise<string> {
        try {
            const condaPath = path.join(this.miniforgeDir, 'bin', 'conda');
            const { stdout } = await execAsync(`"${condaPath}" run -n ${this.brainEnvName} python -c "import ghost_brain; print(ghost_brain.__version__)"`);
            return stdout.trim();
        } catch {
            return 'Unknown';
        }
    }

    /**
     * Download a file from URL
     */
    private async downloadFile(url: string, filePath: string): Promise<void> {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to download ${url}: ${response.statusText}`);
        }
        
        const buffer = await response.arrayBuffer();
        fs.writeFileSync(filePath, Buffer.from(buffer));
    }
} 