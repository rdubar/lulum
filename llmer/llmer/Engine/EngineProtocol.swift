//
//  EngineProtocol.swift
//  llmer
//
//  Created by Roger Dubar on 27/03/2026.
//

import Foundation

protocol Engine: AnyObject {
    var name: String { get }
    var isModelLoaded: Bool { get }

    func isAvailable() async -> Bool
    func listModels() async -> [ModelInfo]
    func loadModel(_ name: String) async throws
    func generate(messages: [ChatMessage]) -> AsyncThrowingStream<String, Error>
    func unload() async
}

enum EngineError: LocalizedError {
    case noModelLoaded

    var errorDescription: String? {
        switch self {
        case .noModelLoaded:
            return "No model loaded. Select a model first."
        }
    }
}
