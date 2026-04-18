//
//  MLXEngine.swift
//  llmer
//
//  Created by Roger Dubar on 27/03/2026.
//

import Foundation
import MLXLLM
import MLXLMCommon

final class MLXEngine: Engine {
    let name = "mlx"

    private var chatSession: ChatSession?
    private var modelContainer: ModelContainer?
    private var loadedModelName: String?

    var isModelLoaded: Bool { chatSession != nil }

    static let recommendedModels: [ModelInfo] = [
        ModelInfo(id: "mlx-community/Llama-3.2-1B-Instruct-4bit", name: "Llama-3.2-1B-Instruct-4bit",
                  displayName: "Llama 3.2 1B", engine: "mlx", size: "~0.7 GB"),
        ModelInfo(id: "mlx-community/Llama-3.2-3B-Instruct-4bit", name: "Llama-3.2-3B-Instruct-4bit",
                  displayName: "Llama 3.2 3B", engine: "mlx", size: "~1.8 GB"),
        ModelInfo(id: "mlx-community/gemma-2-2b-it-4bit", name: "gemma-2-2b-it-4bit",
                  displayName: "Gemma 2 2B", engine: "mlx", size: "~1.4 GB"),
        ModelInfo(id: "mlx-community/Qwen3-4B-4bit", name: "Qwen3-4B-4bit",
                  displayName: "Qwen 3 4B", engine: "mlx", size: "~2.5 GB"),
    ]

    func isAvailable() async -> Bool {
        true
    }

    func listModels() async -> [ModelInfo] {
        Self.recommendedModels
    }

    func loadModel(_ name: String) async throws {
        let modelConfig = ModelConfiguration(id: name)
        let container = try await LLMModelFactory.shared.loadContainer(
            configuration: modelConfig
        ) { progress in
            Task { @MainActor in
                NotificationCenter.default.post(
                    name: .mlxModelDownloadProgress,
                    object: nil,
                    userInfo: ["progress": progress.fractionCompleted]
                )
            }
        }
        modelContainer = container
        chatSession = ChatSession(container)
        loadedModelName = name
    }

    func generate(messages: [ChatMessage]) -> AsyncThrowingStream<String, Error> {
        guard let session = chatSession else {
            return AsyncThrowingStream { $0.finish(throwing: EngineError.noModelLoaded) }
        }

        let prompt = messages.last?.content ?? ""

        return AsyncThrowingStream { continuation in
            Task {
                do {
                    for try await text in session.streamResponse(to: prompt) {
                        continuation.yield(text)
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

    func unload() async {
        chatSession = nil
        modelContainer = nil
        loadedModelName = nil
    }
}

extension Notification.Name {
    static let mlxModelDownloadProgress = Notification.Name("mlxModelDownloadProgress")
}
