import { Setting } from "obsidian";
import GhostGPT, { GhostSettings } from "src/main";

export function addBrainServerSettings(
    containerEl: HTMLElement,
    plugin: GhostGPT,
    settings: GhostSettings
) {
    const brainServerContainer = containerEl.createDiv("brain-server-settings");
    
    // Header
    const headerEl = brainServerContainer.createEl("h3", { text: "Brain Server Settings" });
    headerEl.style.marginTop = "1rem";
    headerEl.style.marginBottom = "0.5rem";

    // Description
    const descriptionEl = brainServerContainer.createEl("p", {
        text: "Configure your brain server connection. Use custom server for remote or cloud deployments."
    });
    descriptionEl.style.fontSize = "0.8rem";
    descriptionEl.style.color = "var(--text-muted)";
    descriptionEl.style.marginBottom = "1rem";

    // Toggle for custom brain server
    new Setting(brainServerContainer)
        .setName("Use Custom Brain Server")
        .setDesc("Connect to brain server running elsewhere (cloud, remote desktop, etc.)")
        .addToggle(toggle => {
            toggle.setValue(settings.brainServer.useCustomBrainServer)
                .onChange(async (value) => {
                    settings.brainServer.useCustomBrainServer = value;
                    await plugin.saveSettings();
                    
                    // Refresh the settings display to show/hide URL field
                    const urlSetting = brainServerContainer.querySelector('.brain-server-url-setting');
                    if (urlSetting) {
                        urlSetting.style.display = value ? 'block' : 'none';
                    }
                });
        });

    // Custom brain server URL setting
    const urlSettingContainer = brainServerContainer.createDiv("brain-server-url-setting");
    urlSettingContainer.style.display = settings.brainServer.useCustomBrainServer ? 'block' : 'none';
    
    new Setting(urlSettingContainer)
        .setName("Brain Server URL")
        .setDesc("Full URL to your brain server (e.g., https://my-brain.com or http://192.168.1.100:8000)")
        .addText(text => {
            text.setValue(settings.brainServer.brainServerUrl)
                .setPlaceholder("https://my-brain-server.com")
                .onChange(async (value) => {
                    settings.brainServer.brainServerUrl = value;
                    await plugin.saveSettings();
                });
        });

    // Local brain server port setting (only show when not using custom server)
    const portSettingContainer = brainServerContainer.createDiv("brain-server-port-setting");
    portSettingContainer.style.display = settings.brainServer.useCustomBrainServer ? 'none' : 'block';
    
    new Setting(portSettingContainer)
        .setName("Local Brain Server Port")
        .setDesc("Port for local brain server (default: 8000)")
        .addText(text => {
            text.setValue(settings.brainServer.brainServerPort.toString())
                .setPlaceholder("8000")
                .onChange(async (value) => {
                    const port = parseInt(value) || 8000;
                    settings.brainServer.brainServerPort = port;
                    await plugin.saveSettings();
                });
        });

    // Chat history path setting
    const chatHistoryContainer = brainServerContainer.createDiv("chat-history-path-setting");
    
    new Setting(chatHistoryContainer)
        .setName("Chat History Path")
        .setDesc("Path to nexus-ai-chat-importer chat logs (e.g., ref/chatlogs or BMO/History)")
        .addText(text => {
            text.setValue(settings.brainServer.chatHistoryPath)
                .setPlaceholder("ref/chatlogs")
                .onChange(async (value) => {
                    settings.brainServer.chatHistoryPath = value;
                    await plugin.saveSettings();
                });
        });

    // Chat history info
    const chatHistoryInfo = chatHistoryContainer.createEl("p", {
        text: "💡 The brain will embed and index all chat logs in this folder for semantic search. Supports nested year/month structure.",
        attr: { 
            style: "font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem; padding: 0.5rem; background: var(--background-secondary-alt); border-radius: 4px;" 
        }
    });

    // Embed chat history button
    const embedButton = chatHistoryContainer.createEl("button", {
        text: "Embed Chat History",
        attr: { 
            style: "margin-top: 0.5rem; padding: 0.5rem 1rem; font-size: 0.8rem; border-radius: 4px; border: 1px solid var(--text-muted); background: var(--background-primary); color: var(--text-normal); cursor: pointer;" 
        }
    });
    
    embedButton.addEventListener("click", async () => {
        embedButton.textContent = "Embedding...";
        embedButton.disabled = true;
        
        try {
            const brainUrl = settings.brainServer.useCustomBrainServer 
                ? settings.brainServer.brainServerUrl 
                : `http://localhost:${settings.brainServer.brainServerPort}`;
            
            const response = await fetch(`${brainUrl}/chat-history/embed`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chat_history_path: settings.brainServer.chatHistoryPath,
                    user_id: 'obsidian_user'
                }),
            });

            if (response.ok) {
                const result = await response.json();
                
                // Show results
                const resultsContainer = chatHistoryContainer.createDiv("embed-results");
                resultsContainer.style.marginTop = "1rem";
                resultsContainer.style.padding = "0.5rem";
                resultsContainer.style.backgroundColor = result.status === "success" ? "var(--background-success)" : "var(--background-error)";
                resultsContainer.style.borderRadius = "4px";
                resultsContainer.style.fontSize = "0.8rem";
                
                const resultsText = resultsContainer.createEl("p", {
                    text: `✅ Embedded ${result.chunks_embedded} chunks from ${result.files_processed} files${result.chunks_skipped > 0 ? ` (${result.chunks_skipped} skipped - already exist)` : ''}`,
                    attr: { style: "margin: 0; font-weight: bold;" }
                });
                
                if (result.errors && result.errors.length > 0) {
                    const errorsText = resultsContainer.createEl("p", {
                        text: `⚠️ ${result.errors.length} errors occurred`,
                        attr: { style: "margin: 0.3rem 0 0 0; font-size: 0.7rem;" }
                    });
                }
                
                // Remove results after 10 seconds
                setTimeout(() => {
                    if (resultsContainer.parentNode) {
                        resultsContainer.remove();
                    }
                }, 10000);
                
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error embedding chat history:', error);
            
            // Show error
            const errorContainer = chatHistoryContainer.createDiv("embed-error");
            errorContainer.style.marginTop = "1rem";
            errorContainer.style.padding = "0.5rem";
            errorContainer.style.backgroundColor = "var(--background-error)";
            errorContainer.style.borderRadius = "4px";
            errorContainer.style.fontSize = "0.8rem";
            
            const errorText = errorContainer.createEl("p", {
                text: `❌ Error embedding chat history: ${error.message}`,
                attr: { style: "margin: 0;" }
            });
            
            // Remove error after 10 seconds
            setTimeout(() => {
                if (errorContainer.parentNode) {
                    errorContainer.remove();
                }
            }, 10000);
        } finally {
            embedButton.textContent = "Embed Chat History";
            embedButton.disabled = false;
        }
    });

    // Status indicator
    const statusContainer = brainServerContainer.createDiv("brain-server-status");
    statusContainer.style.marginTop = "1rem";
    statusContainer.style.padding = "0.5rem";
    statusContainer.style.borderRadius = "4px";
    statusContainer.style.backgroundColor = "var(--background-secondary)";
    
    const statusText = statusContainer.createEl("p", {
        text: "Checking brain server status...",
        attr: { style: "margin: 0; font-size: 0.8rem;" }
    });

    // Check brain server status
    const checkBrainStatus = async () => {
        try {
            const brainUrl = settings.brainServer.useCustomBrainServer 
                ? settings.brainServer.brainServerUrl 
                : `http://localhost:${settings.brainServer.brainServerPort}`;
            
            const response = await fetch(`${brainUrl}/health`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            });

            if (response.ok) {
                statusContainer.style.backgroundColor = "var(--background-success)";
                statusText.textContent = `✅ Brain server connected at ${brainUrl}`;
            } else {
                statusContainer.style.backgroundColor = "var(--background-error)";
                statusText.textContent = `❌ Brain server not responding at ${brainUrl}`;
            }
        } catch (error) {
            statusContainer.style.backgroundColor = "var(--background-error)";
            statusText.textContent = `❌ Cannot connect to brain server`;
        }
    };

    // Check status immediately and every 30 seconds
    checkBrainStatus();
    setInterval(checkBrainStatus, 30000);

    // Refresh button
    const refreshButton = statusContainer.createEl("button", {
        text: "Refresh Status",
        attr: { 
            style: "margin-left: 0.5rem; padding: 0.2rem 0.5rem; font-size: 0.7rem; border-radius: 3px; border: 1px solid var(--text-muted); background: var(--background-primary); color: var(--text-normal); cursor: pointer;" 
        }
    });
    
    refreshButton.addEventListener("click", checkBrainStatus);

    // Help text
    const helpContainer = brainServerContainer.createDiv("brain-server-help");
    helpContainer.style.marginTop = "1rem";
    helpContainer.style.padding = "0.5rem";
    helpContainer.style.backgroundColor = "var(--background-secondary-alt)";
    helpContainer.style.borderRadius = "4px";
    helpContainer.style.fontSize = "0.7rem";
    
    const helpText = helpContainer.createEl("p", {
        text: "💡 Tips:",
        attr: { style: "margin: 0 0 0.3rem 0; font-weight: bold;" }
    });
    
    const tip1 = helpContainer.createEl("p", {
        text: "• For mobile: Install brain on your desktop and use your desktop's IP address",
        attr: { style: "margin: 0.1rem 0;" }
    });
    
    const tip2 = helpContainer.createEl("p", {
        text: "• For cloud: Deploy brain on Railway, Heroku, or any cloud service",
        attr: { style: "margin: 0.1rem 0;" }
    });
    
    const tip3 = helpContainer.createEl("p", {
        text: "• For team: Share one brain server with multiple team members",
        attr: { style: "margin: 0.1rem 0;" }
    });

    const noteContainer = brainServerContainer.createDiv("brain-server-note");
    noteContainer.style.marginTop = "0.5rem";
    noteContainer.style.padding = "0.5rem";
    noteContainer.style.backgroundColor = "var(--background-modifier-warning)";
    noteContainer.style.borderRadius = "4px";
    noteContainer.style.fontSize = "0.7rem";
    noteContainer.style.border = "1px solid var(--text-warning)";
    
    const noteText = noteContainer.createEl("p", {
        text: "⚠️ Note: After changing brain server settings, reopen the chat view for changes to take effect.",
        attr: { style: "margin: 0; color: var(--text-warning);" }
    });
} 