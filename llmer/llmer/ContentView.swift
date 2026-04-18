//
//  ContentView.swift
//  llmer
//
//  Created by Roger Dubar on 27/03/2026.
//

import SwiftUI

struct ContentView: View {
    @State private var viewModel = ChatViewModel()
    @State private var showModelPicker = false

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.hasModel {
                    ChatView(viewModel: viewModel)
                } else {
                    welcomeView
                }
            }
            .navigationTitle("llmer")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showModelPicker = true
                    } label: {
                        Label(
                            viewModel.selectedModel?.displayName ?? "No Model",
                            systemImage: "cpu"
                        )
                    }
                }

                if viewModel.hasModel {
                    ToolbarItem(placement: .automatic) {
                        Button {
                            viewModel.clearHistory()
                        } label: {
                            Label("Clear", systemImage: "trash")
                        }
                    }
                }
            }
            .sheet(isPresented: $showModelPicker) {
                NavigationStack {
                    ModelPickerView(viewModel: viewModel)
                        .toolbar {
                            ToolbarItem(placement: .confirmationAction) {
                                Button("Done") { showModelPicker = false }
                            }
                        }
                }
                .presentationDetents([.medium, .large])
            }
        }
    }

    private var welcomeView: some View {
        VStack(spacing: 16) {
            Image(systemName: "cube")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("llmer")
                .font(.largeTitle.bold())
            Text("Local LLM inference")
                .foregroundStyle(.secondary)
            Button("Select a Model") {
                showModelPicker = true
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}

#Preview {
    ContentView()
}
