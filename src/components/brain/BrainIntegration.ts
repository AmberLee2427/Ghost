import BMOGPT, { BMOSettings } from 'src/main';

export interface BrainMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    message_id?: string;
    timestamp?: string;
    author_id?: string;
}

export interface BrainResponse {
    response: string;
    reasoning?: string;
    memory_chunks: number;
    timestamp: string;
    model_type: string;
    model_name: string;
    memory_backend: string;
}

export class BrainIntegration {
    private plugin: BMOGPT;
    private settings: BMOSettings;
    private brainUrl: string;
    private isInitialized: boolean = false;

    constructor(plugin: BMOGPT, settings: BMOSettings) {
        this.plugin = plugin;
        this.settings = settings;
        // Default brain URL - can be made configurable later
        this.brainUrl = 'http://localhost:8000';
    }

    async initialize(): Promise<boolean> {
        try {
            // Test brain connectivity
            const response = await fetch(`${this.brainUrl}/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                this.isInitialized = true;
                console.log('Brain integration initialized successfully');
                return true;
            } else {
                console.warn('Brain not available, falling back to local mode');
                return false;
            }
        } catch (error) {
            console.warn('Brain not available, falling back to local mode:', error);
            return false;
        }
    }

    async processMessage(
        message: string, 
        history: BrainMessage[] = [],
        userId: string = 'obsidian_user'
    ): Promise<BrainResponse | null> {
        if (!this.isInitialized) {
            console.warn('Brain not initialized, cannot process message');
            return null;
        }

        try {
            const requestBody = {
                message: message,
                history: history,
                user_id: userId,
                system_prompt: this.settings.general.system_role,
                model_type: this.getModelType(),
                model_name: this.settings.general.model,
                use_structured_response: false
            };

            const response = await fetch(`${this.brainUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            if (response.ok) {
                const result = await response.json();
                return result as BrainResponse;
            } else {
                console.error('Brain processing failed:', response.statusText);
                return null;
            }
        } catch (error) {
            console.error('Error processing message with brain:', error);
            return null;
        }
    }

    async searchMemory(query: string, topK: number = 3): Promise<string[]> {
        if (!this.isInitialized) {
            return [];
        }

        try {
            const response = await fetch(`${this.brainUrl}/memory/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    top_k: topK
                }),
            });

            if (response.ok) {
                const result = await response.json();
                return result.chunks || [];
            } else {
                console.error('Memory search failed:', response.statusText);
                return [];
            }
        } catch (error) {
            console.error('Error searching memory:', error);
            return [];
        }
    }

    async getMemoryStats(): Promise<any> {
        if (!this.isInitialized) {
            return null;
        }

        try {
            const response = await fetch(`${this.brainUrl}/memory/stats`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                return await response.json();
            } else {
                console.error('Failed to get memory stats:', response.statusText);
                return null;
            }
        } catch (error) {
            console.error('Error getting memory stats:', error);
            return null;
        }
    }

    private getModelType(): string {
        const model = this.settings.general.model;
        
        if (this.settings.OllamaConnection.ollamaModels.includes(model)) {
            return 'ollama';
        } else if (this.settings.RESTAPIURLConnection.RESTAPIURLModels.includes(model)) {
            return 'rest_api';
        } else if (this.settings.APIConnections.anthropic.anthropicModels.includes(model)) {
            return 'anthropic';
        } else if (this.settings.APIConnections.googleGemini.geminiModels.includes(model)) {
            return 'google_gemini';
        } else if (this.settings.APIConnections.mistral.mistralModels.includes(model)) {
            return 'mistral';
        } else if (this.settings.APIConnections.openAI.openAIBaseModels.includes(model)) {
            return 'openai';
        } else if (this.settings.APIConnections.openRouter.openRouterModels.includes(model)) {
            return 'openrouter';
        } else {
            return 'auto';
        }
    }

    isAvailable(): boolean {
        return this.isInitialized;
    }
}

// Convert Obsidian message format to brain format
export function convertToBrainMessages(obsidianMessages: { role: string; content: string }[]): BrainMessage[] {
    return obsidianMessages.map((msg, index) => ({
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        message_id: `obsidian_${Date.now()}_${index}`,
        timestamp: new Date().toISOString(),
        author_id: msg.role === 'user' ? 'user' : 'assistant'
    }));
}

// Convert brain response to Obsidian format
export function convertFromBrainResponse(brainResponse: BrainResponse): { role: string; content: string } {
    return {
        role: 'assistant',
        content: brainResponse.response
    };
} 