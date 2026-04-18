//
//  ModelPickerView.swift
//  llmer
//
//  Created by Roger Dubar on 27/03/2026.
//

import SwiftUI

struct ModelPickerView: View {
    @Bindable var viewModel: ChatViewModel

    var body: some View {
        List {
            Section {
                ForEach(viewModel.availableModels) { model in
                    Button {
                        Task { await viewModel.selectModel(model) }
                    } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(model.displayName)
                                    .font(.headline)
                                if let size = model.size {
                                    Text(size)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }

                            Spacer()

                            if viewModel.selectedModel == model {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(.green)
                            }
                        }
                    }
                    .disabled(viewModel.isLoadingModel)
                }
            } header: {
                Text("MLX Models")
            } footer: {
                Text("Models are downloaded from Hugging Face on first use.")
            }

            if viewModel.isLoadingModel {
                Section {
                    VStack(spacing: 8) {
                        ProgressView(value: viewModel.downloadProgress) {
                            Text("Downloading model...")
                        }
                        if let progress = viewModel.downloadProgress {
                            Text("\(Int(progress * 100))%")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                }
            }

            if let error = viewModel.errorMessage {
                Section {
                    Label(error, systemImage: "exclamationmark.triangle")
                        .foregroundStyle(.red)
                }
            }
        }
        .navigationTitle("Models")
        .task { await viewModel.loadModels() }
    }
}
