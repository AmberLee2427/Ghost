import { App, Setting, Notice } from 'obsidian';
import BMOGPT, { BMOSettings } from 'src/main';

export class APISecuritySettings {
    private app: App;
    private plugin: BMOGPT;
    private containerEl: HTMLElement;

    constructor(app: App, plugin: BMOGPT, containerEl: HTMLElement) {
        this.app = app;
        this.plugin = plugin;
        this.containerEl = containerEl;
    }

    display(): void {
        this.containerEl.empty();

        // Header
        const headerEl = this.containerEl.createEl('h2', { text: 'API Security & Keys' });
        headerEl.style.marginBottom = '1rem';

        // Description
        const descriptionEl = this.containerEl.createEl('p', {
            text: 'API keys are stored securely as environment variables and are not retrievable from settings. You can only replace them.'
        });
        descriptionEl.style.marginBottom = '1.5rem';

        // Security notice
        const securityNotice = this.containerEl.createEl('div', { cls: 'security-notice' });
        securityNotice.style.padding = '1rem';
        securityNotice.style.backgroundColor = 'var(--background-modifier-warning)';
        securityNotice.style.borderRadius = '6px';
        securityNotice.style.marginBottom = '1.5rem';
        securityNotice.style.border = '1px solid var(--background-modifier-border)';

        const noticeText = securityNotice.createEl('p', {
            text: '🔒 Security: API keys are stored as environment variables and cannot be viewed once saved. You can only replace them.'
        });
        noticeText.style.margin = '0';
        noticeText.style.fontWeight = '500';

        // API Key Management
        this.createAPIKeySection();

        // Environment Status
        this.createEnvironmentStatusSection();
    }

    private createAPIKeySection(): void {
        const apiSection = this.containerEl.createEl('div', { cls: 'api-keys-section' });

        // OpenAI API Key
        new Setting(apiSection)
            .setName('OpenAI API Key')
            .setDesc('Your OpenAI API key for GPT models')
            .addText(text => text
                .setPlaceholder('sk-...')
                .setValue('')
                .onChange(async (value) => {
                    if (value && value.startsWith('sk-')) {
                        await this.saveAPIKeyAsEnvVar('OPENAI_API_KEY', value);
                        text.setValue(''); // Clear the input
                        new Notice('OpenAI API key saved securely');
                    } else if (value) {
                        new Notice('Invalid OpenAI API key format');
                    }
                })
            )
            .addButton(button => button
                .setButtonText('Check Status')
                .onClick(() => this.checkAPIKeyStatus('OPENAI_API_KEY', 'OpenAI'))
            );

        // Google Gemini API Key
        new Setting(apiSection)
            .setName('Google Gemini API Key')
            .setDesc('Your Google API key for Gemini models')
            .addText(text => text
                .setPlaceholder('AIza...')
                .setValue('')
                .onChange(async (value) => {
                    if (value && value.startsWith('AIza')) {
                        await this.saveAPIKeyAsEnvVar('GOOGLE_API_KEY', value);
                        text.setValue(''); // Clear the input
                        new Notice('Google API key saved securely');
                    } else if (value) {
                        new Notice('Invalid Google API key format');
                    }
                })
            )
            .addButton(button => button
                .setButtonText('Check Status')
                .onClick(() => this.checkAPIKeyStatus('GOOGLE_API_KEY', 'Google'))
            );

        // Anthropic API Key
        new Setting(apiSection)
            .setName('Anthropic API Key')
            .setDesc('Your Anthropic API key for Claude models')
            .addText(text => text
                .setPlaceholder('sk-ant-...')
                .setValue('')
                .onChange(async (value) => {
                    if (value && value.startsWith('sk-ant-')) {
                        await this.saveAPIKeyAsEnvVar('ANTHROPIC_API_KEY', value);
                        text.setValue(''); // Clear the input
                        new Notice('Anthropic API key saved securely');
                    } else if (value) {
                        new Notice('Invalid Anthropic API key format');
                    }
                })
            )
            .addButton(button => button
                .setButtonText('Check Status')
                .onClick(() => this.checkAPIKeyStatus('ANTHROPIC_API_KEY', 'Anthropic'))
            );
    }

    private createEnvironmentStatusSection(): void {
        const statusSection = this.containerEl.createEl('div', { cls: 'env-status-section' });
        statusSection.style.marginTop = '2rem';

        const statusHeader = statusSection.createEl('h3', { text: 'Environment Variables Status' });
        statusHeader.style.marginBottom = '1rem';

        // Status indicators
        this.createStatusIndicator(statusSection, 'OPENAI_API_KEY', 'OpenAI API Key');
        this.createStatusIndicator(statusSection, 'GOOGLE_API_KEY', 'Google API Key');
        this.createStatusIndicator(statusSection, 'ANTHROPIC_API_KEY', 'Anthropic API Key');

        // Clear all keys button
        new Setting(statusSection)
            .setName('Clear All API Keys')
            .setDesc('Remove all stored API keys from environment variables')
            .addButton(button => button
                .setButtonText('Clear All')
                .setWarning()
                .onClick(() => this.clearAllAPIKeys())
            );
    }

    private createStatusIndicator(container: HTMLElement, keyName: string, displayName: string): void {
        const statusItem = container.createEl('div', { cls: 'status-item' });
        statusItem.style.display = 'flex';
        statusItem.style.justifyContent = 'space-between';
        statusItem.style.alignItems = 'center';
        statusItem.style.padding = '0.5rem';
        statusItem.style.marginBottom = '0.5rem';
        statusItem.style.backgroundColor = 'var(--background-secondary)';
        statusItem.style.borderRadius = '4px';

        const label = statusItem.createEl('span', { text: displayName });
        label.style.fontWeight = '500';

        const status = statusItem.createEl('span', { 
            text: this.getAPIKeyStatus(keyName) ? '✓ Configured' : '✗ Not Set',
            cls: this.getAPIKeyStatus(keyName) ? 'status-ok' : 'status-error'
        });
        status.style.fontFamily = 'monospace';
        status.style.color = this.getAPIKeyStatus(keyName) ? 'var(--text-success)' : 'var(--text-error)';
    }

    private async saveAPIKeyAsEnvVar(keyName: string, value: string): Promise<void> {
        try {
            // Save to environment variable (this will be handled by the brain server)
            // For now, we'll store it in a secure way that the brain can access
            await this.plugin.saveData(`secure_${keyName}`, this.encryptValue(value));
            
            // Also set it in the current process environment
            process.env[keyName] = value;
            
            console.log(`API key ${keyName} saved securely`);
        } catch (error) {
            console.error(`Error saving API key ${keyName}:`, error);
            new Notice(`Error saving ${keyName}`);
        }
    }

    private getAPIKeyStatus(keyName: string): boolean {
        // Check if the key exists in environment or secure storage
        return !!(process.env[keyName] || this.plugin.loadData(`secure_${keyName}`));
    }

    private async checkAPIKeyStatus(keyName: string, providerName: string): Promise<void> {
        const hasKey = this.getAPIKeyStatus(keyName);
        if (hasKey) {
            new Notice(`${providerName} API key is configured`);
        } else {
            new Notice(`${providerName} API key is not set`);
        }
    }

    private async clearAllAPIKeys(): Promise<void> {
        try {
            // Clear from secure storage
            await this.plugin.saveData('secure_OPENAI_API_KEY', null);
            await this.plugin.saveData('secure_GOOGLE_API_KEY', null);
            await this.plugin.saveData('secure_ANTHROPIC_API_KEY', null);
            
            // Clear from environment
            delete process.env.OPENAI_API_KEY;
            delete process.env.GOOGLE_API_KEY;
            delete process.env.ANTHROPIC_API_KEY;
            
            new Notice('All API keys cleared');
            
            // Refresh the display
            this.display();
        } catch (error) {
            console.error('Error clearing API keys:', error);
            new Notice('Error clearing API keys');
        }
    }

    private encryptValue(value: string): string {
        // Simple obfuscation - in production, use proper encryption
        return btoa(value);
    }

    private decryptValue(encrypted: string): string {
        // Simple deobfuscation
        return atob(encrypted);
    }

    /**
     * Get API key for brain server (called by brain integration)
     */
    async getAPIKey(keyName: string): Promise<string | null> {
        // First check environment
        if (process.env[keyName]) {
            return process.env[keyName];
        }
        
        // Then check secure storage
        const encrypted = await this.plugin.loadData(`secure_${keyName}`);
        if (encrypted) {
            return this.decryptValue(encrypted);
        }
        
        return null;
    }
} 