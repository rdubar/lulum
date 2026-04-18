//
//  ChatViewModel.swift
//  llmer
//
//  Created by Roger Dubar on 27/03/2026.
//

import Foundation
import SwiftUI

@Observable
final class ChatViewModel {
    var messages: [ChatMessage] = []
    var isGenerating = false
    var currentInput = ""
    var selectedModel: ModelInfo?
    var availableModels: [ModelInfo] = []
    var isLoadingModel = false
    var downloadProgress: Double?
    var errorMessage: String?

    private let engine = MLXEngine()

    var hasModel: Bool { engine.isModelLoaded }

    @MainActor
    func loadModels() async {
        availableModels = await engine.listModels()
    }

    @MainActor
    func selectModel(_ model: ModelInfo) async {
        isLoadingModel = true
        downloadProgress = 0
        errorMessage = nil

        let observer = NotificationCenter.default.addObserver(
            forName: .mlxModelDownloadProgress,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            if let progress = notification.userInfo?["progress"] as? Double {
                self?.downloadProgress = progress
            }
        }

        do {
            try await engine.loadModel(model.id)
            selectedModel = model
        } catch {
            errorMessage = error.localizedDescription
        }

        NotificationCenter.default.removeObserver(observer)
        isLoadingModel = false
        downloadProgress = nil
    }

    @MainActor
    func send() async {
        let text = currentInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isGenerating else { return }

        currentInput = ""
        messages.append(ChatMessage(role: .user, content: text))
        messages.append(ChatMessage(role: .assistant, content: ""))
        isGenerating = true
        errorMessage = nil

        do {
            let allMessages = Array(messages.dropLast())
            for try await chunk in engine.generate(messages: allMessages) {
                if let lastIndex = messages.indices.last {
                    messages[lastIndex].content += chunk
                }
            }
        } catch {
            errorMessage = error.localizedDescription
            if messages.last?.content.isEmpty == true {
                messages.removeLast()
            }
        }

        isGenerating = false
    }

    func clearHistory() {
        messages.removeAll()
    }
}
