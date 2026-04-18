//
//  ModelInfo.swift
//  llmer
//
//  Created by Roger Dubar on 27/03/2026.
//

import Foundation

struct ModelInfo: Identifiable, Hashable {
    let id: String
    let name: String
    let displayName: String
    let engine: String
    let size: String?

    init(id: String, name: String, displayName: String? = nil, engine: String, size: String? = nil) {
        self.id = id
        self.name = name
        self.displayName = displayName ?? name
        self.engine = engine
        self.size = size
    }
}
