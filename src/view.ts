import {
	ItemView,
	WorkspaceLeaf,
	TFile,
	MarkdownView,
	Editor,
	EditorPosition,
} from "obsidian";
import { DEFAULT_SETTINGS, BMOSettings } from "./main";
import BMOGPT from "./main";
import { executeCommand } from "./components/chat/Commands";
import { getActiveFileContent } from "./components/editor/ReferenceCurrentNote";
import { addMessage } from "./components/chat/Message";
import { displayUserMessage } from "./components/chat/UserMessage";
import {
	displayBotMessage,
	displayErrorBotMessage,
} from "./components/chat/BotMessage";
import {
	fetchOpenAIAPIResponseStream,
	fetchOpenAIAPIResponse,
	fetchOllamaResponse,
	fetchOllamaResponseStream,
	fetchRESTAPIURLResponse,
	fetchRESTAPIURLResponseStream,
	fetchMistralResponse,
	fetchMistralResponseStream,
	fetchGoogleGeminiResponse,
	fetchAnthropicResponse,
	fetchOpenRouterResponseStream,
	fetchOpenRouterResponse,
} from "./components/FetchModelResponse";
import { MessageManager } from "./components/brain/MessageManager";

export const VIEW_TYPE_CHATBOT = "chatbot-view";
export const ANTHROPIC_MODELS = [
	"claude-instant-1.2",
	"claude-2.0",
	"claude-2.1",
	"claude-3-opus-20240229",
	"claude-3-sonnet-20240229",
];
export const OPENAI_MODELS = [
	"gpt-3.5-turbo",
	"gpt-3.5-turbo-1106",
	"gpt-4",
	"gpt-4-turbo-preview",
	"gpt-4-turbo",
	"gpt-4-turbo-2024-04-09",
	"gpt-4o",
	"gpt-4o-2024-05-13",
];

// Legacy function for backward compatibility - now uses MessageManager
export function filenameMessageHistoryJSON(plugin: BMOGPT) {
	const filenameMessageHistoryPath = "./.obsidian/plugins/bmo-chatbot/data/";
	const currentProfileMessageHistory =
		"messageHistory_" +
		plugin.settings.profiles.profile.replace(".md", ".json");

	return filenameMessageHistoryPath + currentProfileMessageHistory;
}

// Legacy messageHistory for backward compatibility - now managed by MessageManager
export let messageHistory: { role: string; content: string }[] = [];

export let lastCursorPosition: EditorPosition = {
	line: 0,
	ch: 0,
};

export let lastCursorPositionFile: TFile | null = null;
export let activeEditor: Editor | null | undefined = null;

export class BMOView extends ItemView {
	private settings: BMOSettings;
	private textareaElement: HTMLTextAreaElement;
	private preventEnter = false;
	private plugin: BMOGPT;
	private messageManager: MessageManager;

	constructor(leaf: WorkspaceLeaf, settings: BMOSettings, plugin: BMOGPT) {
		super(leaf);
		this.settings = settings;
		this.plugin = plugin;
		this.icon = "bot";
		this.messageManager = new MessageManager(plugin, settings);
		this.addCursorLogging();
	}

	getViewType() {
		return VIEW_TYPE_CHATBOT;
	}

	getDisplayText() {
		return "My BMO Chatbot";
	}

	async onOpen(): Promise<void> {
		const container = this.containerEl.children[1];
		container.empty();
		const chatbotContainer = container.createEl("div", {
			attr: {
				class: "chatbotContainer",
			},
		});

		const header = chatbotContainer.createEl("div", {
			attr: {
				id: "header",
			},
		});

		const chatbotNameHeading = chatbotContainer.createEl("h1", {
			text:
				this.settings.appearance.chatbotName ||
				DEFAULT_SETTINGS.appearance.chatbotName,
			attr: {
				id: "chatbotNameHeading",
			},
		});

		const modelName = chatbotContainer.createEl("p", {
			text:
				"Model: " + this.settings.general.model ||
				DEFAULT_SETTINGS.general.model,
			attr: {
				id: "modelName",
			},
		});

		const spanElement = chatbotContainer.createEl("span", {
			attr: {
				class: "dotIndicator",
				id: "markDownBoolean",
			},
		});

		const referenceCurrentNoteElement = chatbotContainer.createEl("p", {
			text: "Reference Current Note",
			attr: {
				id: "referenceCurrentNote",
			},
		});

		// Add brain status indicator
		const brainSpanElement = chatbotContainer.createEl("span", {
			attr: {
				class: "dotIndicator",
				id: "brainStatusIndicator",
			},
		});

		const brainStatusElement = chatbotContainer.createEl("p", {
			text: "Brain Server",
			attr: {
				id: "brainStatus",
			},
		});

		header.appendChild(chatbotNameHeading);
		header.appendChild(modelName);

		referenceCurrentNoteElement.appendChild(spanElement);
		brainStatusElement.appendChild(brainSpanElement);

		referenceCurrentNoteElement.style.display = "none";
		brainStatusElement.style.display = "none";

		if (referenceCurrentNoteElement) {
			if (this.settings.general.allowReferenceCurrentNote) {
				referenceCurrentNoteElement.style.display = "block";
			} else {
				referenceCurrentNoteElement.style.display = "none";
			}
		}

		// Show brain status if brain integration is enabled
		if (this.settings.general.allowReferenceCurrentNote) {
			brainStatusElement.style.display = "block";
			this.updateBrainStatusIndicator();
			this.startBrainStatusChecks();
		} else {
			brainStatusElement.style.display = "none";
		}

		const messageContainer = chatbotContainer.createEl("div", {
			attr: {
				id: "messageContainer",
			},
		});

		if (this.settings.appearance.allowHeader) {
			header.style.display = "block";
		} else {
			header.style.display = "none";
			messageContainer.style.maxHeight = "calc(100% - 60px)";
			referenceCurrentNoteElement.style.margin = "0.5rem 0 0.5rem 0";
		}

		// Initialize MessageManager and load messages
		await this.messageManager.initialize();
		
		// Update legacy messageHistory for backward compatibility
		messageHistory = this.messageManager.getMessageHistory();

		// Display messages in the UI
		messageHistory.forEach(async (messageData) => {
			if (messageData.role == "user") {
				const userMessageDiv = displayUserMessage(
					this.plugin,
					this.settings,
					messageData.content,
				);
				messageContainer.appendChild(userMessageDiv);
			}

			if (messageData.role == "assistant") {
				const botMessageDiv = displayBotMessage(
					this.plugin,
					this.settings,
					messageHistory,
					messageData.content,
				);
				messageContainer.appendChild(botMessageDiv);
			}
		});

		// Open notes/links from chatbot
		messageContainer.addEventListener("click", (event) => {
			const target = event.target as HTMLElement;
			if (
				target.tagName === "A" &&
				target.classList.contains("internal-link")
			) {
				event.preventDefault();
				const href = target.getAttribute("href");
				if (href) {
					this.plugin.app.workspace.openLinkText(href, "", true, {
						active: true,
					});
				}
			}
		});

		const chatbox = chatbotContainer.createEl("div", {
			attr: {
				class: "chatbox",
			},
		});

		this.textareaElement = chatbox.createEl("textarea", {
			attr: {
				placeholder: "Type your message here...",
				rows: "3",
			},
		});

		this.addEventListeners();

		// Focus on the textarea
		this.textareaElement.focus();
	}

	addEventListeners() {
		this.textareaElement.addEventListener("keyup", (event) =>
			this.handleKeyup(event),
		);
		this.textareaElement.addEventListener("keydown", (event) =>
			this.handleKeydown(event),
		);
		this.textareaElement.addEventListener("input", (event) =>
			this.handleInput(event),
		);
		this.textareaElement.addEventListener("blur", (event) =>
			this.handleBlur(event),
		);
	}

	async handleKeyup(event: KeyboardEvent) {
		if (event.key === "Enter" && !event.shiftKey) {
			event.preventDefault();
			const input = this.textareaElement.value.trim();

			if (input === "") {
				return;
			}

			// Check if it's a command
			if (input.startsWith("/")) {
				executeCommand(input, this.settings, this.plugin);
				this.textareaElement.value = "";
				return;
			}

			// Clear the textarea
			this.textareaElement.value = "";

			// Add user message to MessageManager
			await this.messageManager.addUserMessage(input);
			
			// Update legacy messageHistory for backward compatibility
			messageHistory = this.messageManager.getMessageHistory();

			// Display user message
			const messageContainer = document.querySelector(
				"#messageContainer",
			) as HTMLDivElement;
			const userMessageDiv = displayUserMessage(
				this.plugin,
				this.settings,
				input,
			);
			messageContainer.appendChild(userMessageDiv);

			// Scroll to bottom
			messageContainer.scrollTop = messageContainer.scrollHeight;

			// Try to process with brain first, fall back to direct API if not available
			let brainResponse = null;
			if (this.messageManager.isBrainAvailable()) {
				try {
					brainResponse = await this.messageManager.processMessageWithBrain(input);
				} catch (error) {
					console.warn("Brain processing failed, falling back to direct API:", error);
				}
			}

			if (brainResponse) {
				// Use brain response
				await this.messageManager.addAssistantMessage(brainResponse);
				messageHistory = this.messageManager.getMessageHistory();
				
				const botMessageDiv = displayBotMessage(
					this.plugin,
					this.settings,
					messageHistory,
					brainResponse,
				);
				messageContainer.appendChild(botMessageDiv);
			} else {
				// Fall back to direct API processing (existing logic)
				await this.BMOchatbot();
			}

			// Scroll to bottom
			messageContainer.scrollTop = messageContainer.scrollHeight;
		}
	}

	handleKeydown(event: KeyboardEvent) {
		if (event.key === "Enter" && !event.shiftKey) {
			this.preventEnter = true;
		}
	}

	handleInput(event: Event) {
		if (this.preventEnter) {
			this.preventEnter = false;
		}
	}

	handleBlur(event: Event) {
		this.preventEnter = false;
	}

	exportSettings() {
		// Settings export logic if needed
	}

	addCursorLogging() {
		const updateCursorPosition = async () => {
			const activeView =
				this.app.workspace.getActiveViewOfType(MarkdownView);
			if (activeView) {
				const editor = activeView.editor;
				const cursor = editor.getCursor();
				lastCursorPosition = cursor;
				lastCursorPositionFile = activeView.file;
				activeEditor = editor;
			}
		};

		this.registerEvent(
			this.app.workspace.on("active-leaf-change", updateCursorPosition),
		);
		this.registerEvent(
			this.app.workspace.on("editor-change", updateCursorPosition),
		);
	}

	cleanup() {
		// Cleanup logic if needed
	}

	/**
	 * Update the brain status indicator
	 */
	async updateBrainStatusIndicator(): Promise<void> {
		const brainIndicator = document.querySelector("#brainStatusIndicator") as HTMLElement;
		if (!brainIndicator) return;

		try {
			// Check if brain server is running
			const response = await fetch('http://localhost:8000/health');
			if (response.ok) {
				// Green dot for brain server running
				brainIndicator.style.backgroundColor = "#4CAF50";
				brainIndicator.title = "Brain server is running and available";
			} else {
				// Yellow dot for brain server responding but not healthy
				brainIndicator.style.backgroundColor = "#FF9800";
				brainIndicator.title = "Brain server responding but not healthy";
			}
		} catch (error) {
			// Red dot for brain server not available
			brainIndicator.style.backgroundColor = "#F44336";
			brainIndicator.title = "Brain server not available";
		}
	}

	/**
	 * Start periodic brain status checks
	 */
	startBrainStatusChecks(): void {
		// Check brain status every 30 seconds
		setInterval(() => {
			this.updateBrainStatusIndicator();
		}, 30000);
	}

	async BMOchatbot() {
		await getActiveFileContent(this.plugin, this.settings);
		const index = messageHistory.length - 1;

		// If model does not exist.
		if (this.settings.general.model === "") {
			const errorMessage = "Model not found.";

			const messageContainer = document.querySelector(
				"#messageContainer",
			) as HTMLDivElement;
			const botMessageDiv = displayErrorBotMessage(
				this.plugin,
				this.settings,
				messageHistory,
				errorMessage,
			);
			messageContainer.appendChild(botMessageDiv);

			const botMessages =
				messageContainer.querySelectorAll(".botMessage");
			const lastBotMessage = botMessages[botMessages.length - 1];
			lastBotMessage.scrollIntoView({
				behavior: "smooth",
				block: "start",
			});
		} else {
			// Fetch OpenAI API
			if (
				this.settings.OllamaConnection.ollamaModels.includes(
					this.settings.general.model,
				)
			) {
				if (this.settings.OllamaConnection.allowStream) {
					await fetchOllamaResponseStream(
						this.plugin,
						this.settings,
						index,
					);
				} else {
					await fetchOllamaResponse(
						this.plugin,
						this.settings,
						index,
					);
				}
			} else if (
				this.settings.RESTAPIURLConnection.RESTAPIURLModels.includes(
					this.settings.general.model,
				)
			) {
				if (this.settings.RESTAPIURLConnection.allowStream) {
					await fetchRESTAPIURLResponseStream(
						this.plugin,
						this.settings,
						index,
					);
				} else {
					await fetchRESTAPIURLResponse(
						this.plugin,
						this.settings,
						index,
					);
				}
			} else if (ANTHROPIC_MODELS.includes(this.settings.general.model)) {
				await fetchAnthropicResponse(this.plugin, this.settings, index);
			} else if (
				this.settings.APIConnections.mistral.mistralModels.includes(
					this.settings.general.model,
				)
			) {
				if (this.settings.APIConnections.mistral.allowStream) {
					await fetchMistralResponseStream(
						this.plugin,
						this.settings,
						index,
					);
				} else {
					await fetchMistralResponse(
						this.plugin,
						this.settings,
						index,
					);
				}
			} else if (
				this.settings.APIConnections.googleGemini.geminiModels.includes(
					this.settings.general.model,
				)
			) {
				await fetchGoogleGeminiResponse(
					this.plugin,
					this.settings,
					index,
				);
			} else if (
				this.settings.APIConnections.openAI.openAIBaseModels.includes(
					this.settings.general.model,
				)
			) {
				if (this.settings.APIConnections.openAI.allowStream) {
					await fetchOpenAIAPIResponseStream(
						this.plugin,
						this.settings,
						index,
					);
				} else {
					await fetchOpenAIAPIResponse(
						this.plugin,
						this.settings,
						index,
					);
				}
			} else if (
				this.settings.APIConnections.openRouter.openRouterModels.includes(
					this.settings.general.model,
				)
			) {
				if (this.settings.APIConnections.openRouter.allowStream) {
					await fetchOpenRouterResponseStream(
						this.plugin,
						this.settings,
						index,
					);
				} else {
					await fetchOpenRouterResponse(
						this.plugin,
						this.settings,
						index,
					);
				}
			} else {
				const errorMessage = "Connection not found.";

				const messageContainer = document.querySelector(
					"#messageContainer",
				) as HTMLDivElement;
				const botMessageDiv = displayErrorBotMessage(
					this.plugin,
					this.settings,
					messageHistory,
					errorMessage,
				);
				messageContainer.appendChild(botMessageDiv);

				const botMessages =
					messageContainer.querySelectorAll(".botMessage");
				const lastBotMessage = botMessages[botMessages.length - 1];
				lastBotMessage.scrollIntoView({
					behavior: "smooth",
					block: "start",
				});
			}
		}
	}

	async onClose() {
		// Nothing to clean up.
	}
}

// Legacy function for backward compatibility - now uses MessageManager
async function loadData(plugin: BMOGPT) {
	// This function is now handled by MessageManager.initialize()
	// Keeping for backward compatibility
}

// Legacy function for backward compatibility - now uses MessageManager
export async function deleteAllMessages(plugin: BMOGPT) {
	const messageContainer = document.querySelector("#messageContainer");
	if (messageContainer) {
		messageContainer.innerHTML = "";
	}
	
	// Clear messages in MessageManager
	// Note: This would need to be called on the MessageManager instance
	// For now, we'll just clear the UI
}
