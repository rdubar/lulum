import Foundation
import FoundationModels

struct Message: Decodable {
    let role: String
    let content: String
}

let inputData = FileHandle.standardInput.readDataToEndOfFile()
guard let messages = try? JSONDecoder().decode([Message].self, from: inputData),
      let userMsg = messages.last(where: { $0.role == "user" }) else {
    fputs("error: expected JSON array of {role, content} objects\n", stderr)
    exit(1)
}

let systemMsg = messages.first(where: { $0.role == "system" })?.content

switch SystemLanguageModel.default.availability {
case .available:
    break
case .unavailable(let reason):
    fputs("error: Apple Intelligence unavailable — \(reason)\n", stderr)
    exit(1)
}

let sem = DispatchSemaphore(value: 0)
var exitCode: Int32 = 0

Task {
    do {
        let session = LanguageModelSession(instructions: systemMsg)
        var previous = ""
        for try await snapshot in session.streamResponse(to: userMsg.content) {
            let current = snapshot.content
            let new = String(current.dropFirst(previous.count))
            if !new.isEmpty {
                print(new, terminator: "")
                fflush(stdout)
                previous = current
            }
        }
        print()
    } catch {
        fputs("error: \(error.localizedDescription)\n", stderr)
        exitCode = 1
    }
    sem.signal()
}

sem.wait()
exit(exitCode)
