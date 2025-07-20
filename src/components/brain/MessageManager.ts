import BMOGPT, { BMOSettings } from 'src/main';
import { BrainIntegration, BrainMessage, convertToBrainMessages, convertFromBrainResponse } from './BrainIntegration';

export interface ObsidianMessage {
    role: string;
    content: string;
}

export class MessageManager {
    private plugin: BMOGPT;
    private settings: BMOSettings;
    private brainIntegration: BrainIntegration;
    private messageHistory: ObsidianMessage[] = [];
    private maxMessages: number = 20; // Rolling 20-message view

    constructor(plugin: BMOGPT, settings: BMOSettings) {
        this.plugin = plugin;
        this.settings = settings;
        this.brainIntegration = new BrainIntegration(plugin, settings);
    }

    async initialize(): Promise<void> {
        // Initialize brain integration
        await this.brainIntegration.initialize();
        
        // Load existing messages (if any) but limit to maxMessages
        await this.loadMessages();
        
        console.log(`MessageManager initialized. Brain available: ${this.brainIntegration.isAvailable()}`);
    }

    async addUserMessage(content: string): Promise<void> {
        const message: ObsidianMessage = {
            role: 'user',
            content: content
        };

        this.messageHistory.push(message);
        this.trimToMaxMessages();
        
        // Save to local storage for UI persistence
        await this.saveMessages();
        
        // Store in brain memory (passive - no user action required)
        if (this.brainIntegration.isAvailable()) {
            try {
                const brainMessages = convertToBrainMessages(this.messageHistory);
                await this.brainIntegration.processMessage(content, brainMessages);
            } catch (error) {
                console.warn('Failed to store message in brain memory:', error);
            }
        }
    }

    async addAssistantMessage(content: string): Promise<void> {
        const message: ObsidianMessage = {
            role: 'assistant',
            content: content
        };

        this.messageHistory.push(message);
        this.trimToMaxMessages();
        
        // Save to local storage for UI persistence
        await this.saveMessages();
        
        // Store in brain memory (passive - no user action required)
        if (this.brainIntegration.isAvailable()) {
            try {
                const brainMessages = convertToBrainMessages(this.messageHistory);
                // Store the assistant response in brain memory
                await this.brainIntegration.processMessage(content, brainMessages);
            } catch (error) {
                console.warn('Failed to store assistant message in brain memory:', error);
            }
        }
    }

    async processMessageWithBrain(userMessage: string): Promise<string | null> {
        if (!this.brainIntegration.isAvailable()) {
            console.warn('Brain not available, cannot process message');
            return null;
        }

        try {
            // Convert current message history to brain format
            const brainMessages = convertToBrainMessages(this.messageHistory);
            
            // Process message with brain
            const brainResponse = await this.brainIntegration.processMessage(
                userMessage, 
                brainMessages,
                'obsidian_user'
            );

            if (brainResponse) {
                // Convert brain response back to Obsidian format
                const obsidianMessage = convertFromBrainResponse(brainResponse);
                return obsidianMessage.content;
            } else {
                console.error('No response from brain');
                return null;
            }
        } catch (error) {
            console.error('Error processing message with brain:', error);
            return null;
        }
    }

    async searchMemory(query: string, topK: number = 3): Promise<string[]> {
        if (!this.brainIntegration.isAvailable()) {
            return [];
        }

        return await this.brainIntegration.searchMemory(query, topK);
    }

    async getMemoryStats(): Promise<any> {
        if (!this.brainIntegration.isAvailable()) {
            return null;
        }

        return await this.brainIntegration.getMemoryStats();
    }

    getMessageHistory(): ObsidianMessage[] {
        return [...this.messageHistory]; // Return copy to prevent external modification
    }

    clearMessages(): void {
        this.messageHistory = [];
        this.saveMessages(); // Save empty array
    }

    isBrainAvailable(): boolean {
        return this.brainIntegration.isAvailable();
    }

    async refreshBrainIntegration(): Promise<void> {
        // Recreate brain integration with updated settings
        this.brainIntegration = new BrainIntegration(this.plugin, this.settings);
        await this.brainIntegration.initialize();
        console.log(`Brain integration refreshed. Available: ${this.brainIntegration.isAvailable()}`);
    }

    private trimToMaxMessages(): void {
        if (this.messageHistory.length > this.maxMessages) {
            // Keep the most recent messages
            this.messageHistory = this.messageHistory.slice(-this.maxMessages);
        }
    }

    private async loadMessages(): Promise<void> {
        try {
            const filename = this.getMessageHistoryFilename();
            
            if (await this.plugin.app.vault.adapter.exists(filename)) {
                const fileContent = await this.plugin.app.vault.adapter.read(filename);
                
                if (fileContent.trim() === "") {
                    this.messageHistory = [];
                } else {
                    const loadedMessages = JSON.parse(fileContent);
                    // Ensure we only load up to maxMessages
                    this.messageHistory = loadedMessages.slice(-this.maxMessages);
                }
            } else {
                this.messageHistory = [];
            }
        } catch (error) {
            console.error('Error loading message history:', error);
            this.messageHistory = [];
        }
    }

    private async saveMessages(): Promise<void> {
        try {
            const filename = this.getMessageHistoryFilename();
            const jsonString = JSON.stringify(this.messageHistory, null, 4);
            await this.plugin.app.vault.adapter.write(filename, jsonString);
        } catch (error) {
            console.error('Error saving message history:', error);
        }
    }

    private getMessageHistoryFilename(): string {
        const filenameMessageHistoryPath = "./.obsidian/plugins/bmo-chatbot/data/";
        const currentProfileMessageHistory = "messageHistory_" + 
            this.plugin.settings.profiles.profile.replace(".md", ".json");
        return filenameMessageHistoryPath + currentProfileMessageHistory;
    }
} 