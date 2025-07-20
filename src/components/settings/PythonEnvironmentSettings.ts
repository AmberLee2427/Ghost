import { App, Setting } from 'obsidian';
import BMOGPT, { BMOSettings } from 'src/main';
import { PythonEnvironmentManager, PythonEnvironmentStatus, InstallationProgress } from '../brain/PythonEnvironmentManager';

export class PythonEnvironmentSettings {
    private app: App;
    private plugin: BMOGPT;
    private containerEl: HTMLElement;
    private envManager: PythonEnvironmentManager;
    private status: PythonEnvironmentStatus | null = null;
    private isInstalling = false;

    constructor(app: App, plugin: BMOGPT, containerEl: HTMLElement) {
        this.app = app;
        this.plugin = plugin;
        this.containerEl = containerEl;
        this.envManager = new PythonEnvironmentManager(plugin, plugin.settings);
    }

    display(): void {
        this.containerEl.empty();

        // Header
        const headerEl = this.containerEl.createEl('h2', { text: 'Python Environment & Brain Server' });
        headerEl.style.marginBottom = '1rem';

        // Description
        const descriptionEl = this.containerEl.createEl('p', {
            text: 'The brain system provides advanced memory management and RAG capabilities. Install the Python environment to enable these features.'
        });
        descriptionEl.style.marginBottom = '1.5rem';

        // Status section
        this.createStatusSection();

        // Actions section
        this.createActionsSection();

        // Refresh status
        this.refreshStatus();
    }

    private createStatusSection(): void {
        const statusContainer = this.containerEl.createEl('div', { cls: 'python-env-status' });
        statusContainer.style.marginBottom = '1.5rem';
        statusContainer.style.padding = '1rem';
        statusContainer.style.border = '1px solid var(--background-modifier-border)';
        statusContainer.style.borderRadius = '6px';
        statusContainer.style.backgroundColor = 'var(--background-secondary)';

        const statusHeader = statusContainer.createEl('h3', { text: 'Environment Status' });
        statusHeader.style.marginTop = '0';
        statusHeader.style.marginBottom = '1rem';

        this.statusEl = statusContainer.createEl('div', { cls: 'status-content' });
    }

    private createActionsSection(): void {
        const actionsContainer = this.containerEl.createEl('div', { cls: 'python-env-actions' });

        // Install button
        new Setting(actionsContainer)
            .setName('Install Python Environment')
            .setDesc('Download and install Miniforge, create brain environment, and install brain package')
            .addButton(button => button
                .setButtonText('Install')
                .setCta()
                .onClick(() => this.installEnvironment())
            );

        // Server controls
        new Setting(actionsContainer)
            .setName('Brain Server')
            .setDesc('Start or stop the brain server')
            .addButton(button => button
                .setButtonText('Start Server')
                .setCta()
                .onClick(() => this.startBrainServer())
            )
            .addButton(button => button
                .setButtonText('Stop Server')
                .setWarning()
                .onClick(() => this.stopBrainServer())
            );

        // Refresh button
        new Setting(actionsContainer)
            .setName('Refresh Status')
            .setDesc('Check current environment and server status')
            .addButton(button => button
                .setButtonText('Refresh')
                .onClick(() => this.refreshStatus())
            );
    }

    private async refreshStatus(): Promise<void> {
        try {
            this.status = await this.envManager.getStatus();
            this.updateStatusDisplay();
        } catch (error) {
            console.error('Error refreshing status:', error);
            this.showError('Failed to refresh status');
        }
    }

    private updateStatusDisplay(): void {
        if (!this.statusEl || !this.status) return;

        this.statusEl.empty();

        const createStatusItem = (label: string, value: string | boolean, status: 'success' | 'warning' | 'error') => {
            const item = this.statusEl.createEl('div', { cls: 'status-item' });
            item.style.display = 'flex';
            item.style.justifyContent = 'space-between';
            item.style.alignItems = 'center';
            item.style.marginBottom = '0.5rem';
            item.style.padding = '0.5rem';
            item.style.borderRadius = '4px';
            item.style.backgroundColor = status === 'success' ? 'var(--background-primary)' : 
                                       status === 'warning' ? 'var(--background-modifier-warning)' : 
                                       'var(--background-modifier-error)';

            const labelEl = item.createEl('span', { text: label });
            labelEl.style.fontWeight = '500';

            const valueEl = item.createEl('span', { 
                text: typeof value === 'boolean' ? (value ? '✓ Installed' : '✗ Not Installed') : value 
            });
            valueEl.style.fontFamily = 'monospace';
        };

        // Miniforge status
        createStatusItem(
            'Miniforge',
            this.status.miniforgeInstalled,
            this.status.miniforgeInstalled ? 'success' : 'error'
        );

        if (this.status.miniforgeInstalled) {
            // Python version
            createStatusItem('Python Version', this.status.pythonVersion || 'Unknown', 'success');

            // Conda version
            createStatusItem('Conda Version', this.status.condaVersion || 'Unknown', 'success');

            // Brain environment
            createStatusItem(
                'Brain Environment',
                this.status.brainEnvironmentExists,
                this.status.brainEnvironmentExists ? 'success' : 'warning'
            );

            if (this.status.brainEnvironmentExists) {
                // Brain package
                createStatusItem(
                    'Brain Package',
                    this.status.brainPackageInstalled,
                    this.status.brainPackageInstalled ? 'success' : 'error'
                );

                if (this.status.brainPackageInstalled) {
                    // Brain version
                    createStatusItem('Brain Version', this.status.brainVersion || 'Unknown', 'success');

                    // Server status
                    createStatusItem(
                        'Brain Server',
                        this.status.brainServerRunning,
                        this.status.brainServerRunning ? 'success' : 'warning'
                    );
                }
            }
        }

        // Summary
        const summaryEl = this.statusEl.createEl('div', { cls: 'status-summary' });
        summaryEl.style.marginTop = '1rem';
        summaryEl.style.padding = '0.75rem';
        summaryEl.style.borderRadius = '4px';
        summaryEl.style.backgroundColor = 'var(--background-primary)';
        summaryEl.style.fontWeight = '500';

        if (this.status.brainServerRunning) {
            summaryEl.textContent = '✅ Brain system is ready and running!';
            summaryEl.style.color = 'var(--text-success)';
        } else if (this.status.brainPackageInstalled) {
            summaryEl.textContent = '⚠️ Brain package installed but server not running';
            summaryEl.style.color = 'var(--text-warning)';
        } else if (this.status.miniforgeInstalled) {
            summaryEl.textContent = '⚠️ Miniforge installed but brain environment not ready';
            summaryEl.style.color = 'var(--text-warning)';
        } else {
            summaryEl.textContent = '❌ Python environment not installed';
            summaryEl.style.color = 'var(--text-error)';
        }
    }

    private async installEnvironment(): Promise<void> {
        if (this.isInstalling) return;

        this.isInstalling = true;
        this.showProgress('Starting installation...');

        try {
            const success = await this.envManager.installEnvironment((progress) => {
                this.showProgress(`${progress.message} (${progress.progress}%)`);
            });

            if (success) {
                this.showSuccess('Installation completed successfully!');
                await this.refreshStatus();
            } else {
                this.showError('Installation failed. Check the console for details.');
            }
        } catch (error) {
            console.error('Installation error:', error);
            this.showError(`Installation failed: ${error instanceof Error ? error.message : String(error)}`);
        } finally {
            this.isInstalling = false;
        }
    }

    private async startBrainServer(): Promise<void> {
        try {
            this.showProgress('Starting brain server...');
            const success = await this.envManager.startBrainServer();
            
            if (success) {
                this.showSuccess('Brain server started successfully!');
                await this.refreshStatus();
            } else {
                this.showError('Failed to start brain server. Check the console for details.');
            }
        } catch (error) {
            console.error('Error starting brain server:', error);
            this.showError(`Failed to start brain server: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    private async stopBrainServer(): Promise<void> {
        try {
            this.showProgress('Stopping brain server...');
            const success = await this.envManager.stopBrainServer();
            
            if (success) {
                this.showSuccess('Brain server stopped successfully!');
                await this.refreshStatus();
            } else {
                this.showError('Failed to stop brain server. Check the console for details.');
            }
        } catch (error) {
            console.error('Error stopping brain server:', error);
            this.showError(`Failed to stop brain server: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    private showProgress(message: string): void {
        // Create or update progress notification
        if (!this.progressEl) {
            this.progressEl = this.containerEl.createEl('div', { cls: 'progress-notification' });
            this.progressEl.style.position = 'fixed';
            this.progressEl.style.top = '20px';
            this.progressEl.style.right = '20px';
            this.progressEl.style.padding = '1rem';
            this.progressEl.style.backgroundColor = 'var(--background-primary)';
            this.progressEl.style.border = '1px solid var(--background-modifier-border)';
            this.progressEl.style.borderRadius = '6px';
            this.progressEl.style.zIndex = '1000';
            this.progressEl.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        }
        
        this.progressEl.textContent = message;
    }

    private showSuccess(message: string): void {
        this.hideProgress();
        // Show success notification (you can implement this as needed)
        console.log('Success:', message);
    }

    private showError(message: string): void {
        this.hideProgress();
        // Show error notification (you can implement this as needed)
        console.error('Error:', message);
    }

    private hideProgress(): void {
        if (this.progressEl) {
            this.progressEl.remove();
            this.progressEl = null;
        }
    }

    private statusEl: HTMLElement | null = null;
    private progressEl: HTMLElement | null = null;
} 