<!-- Human-approved DDL content; this authorization record is in the local P2→A candidate and is not yet present in main or installed. -->
# JIT DDL — FG2 modality provenance

Status: APPROVED_FOR_PRODUCTION_DDL
Pro project ref: xwhtiqmboljkshrtviyw
Authorized manifest: fg2-modality-provenance
Authorized payload SHA: d07c2c9facff1870cde0183247bd1e3695a1db3b
Authorized FG2 modality migration SHA256: sha256:66061202f44ecb429caf93b41303215adb02ded0c04e7bbcae2c4a27fb0d1db2
Backup/PITR gate: BACKUP_PITR_RUNTIME_GATE_REQUIRED
Pro apply gate: APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR
Authorized base SHA: f5b5deb6a49b84fab8e40c4dd9c026963f5a4f0d
Authorized non-auth digest SHA256: sha256:f6a95a32be3c448938021cfc8d17464294a3c838e24ca9884743040d8b0480c8

## Human approval evidence and limits

### DDL content approval and original P1 binding

Approver: Romel, explicit instruction in TL chat 01a2158b-00eb-78e2-a997-9ca65e2bb23d.
Instruction: "aprobado el jit preparado"
Recorded at: 2026-11-26 20:02:21 UTC / 2026-11-26 15:02:21 America/Lima.
Approved draft SHA256: b721ded55b006a48f483d3d5d6d2b833bd53b37f046dac167b21a8daa73c1399.
Original binding: payload 8fc365b398b9fe7f7d8c8bae2f5f3887edc25658; non-auth digest sha256:534f48b5f2cb1c778fdb4b5d6e96d34ce8bb977ca13d863ef4b0d4abf36b82a2.

### P2 payload-binding approval

Approver: Romel, explicit instruction in this conversation.
Instruction: "Apruebo la vinculación JIT al payload P2 d07c2c9facff1870cde0183247bd1e3695a1db3b y digest sha256:f6a95a32be3c448938021cfc8d17464294a3c838e24ca9884743040d8b0480c8, conservando base, proyecto, manifest y SQL de la propuesta P2-PENDING."
Recorded at: 2026-11-26 21:29:44 UTC / 2026-11-26 16:29:44 America/Lima.
Approved binding proposal SHA256: 72272316607ffd23087d4cc28e736816edeb300718065b770b7adcb36c1625c7.
Scope: approves rebinding the payload and non-auth digest to P2. The DDL, project, manifest, migration hash, base and runtime gates remain unchanged.

The P1 approval is preserved as historical evidence and does not authorize P2 by itself. The P2 approval applies to the exact payload and digest above.
This does not authorize push/PR, merge, workflow dispatch, Apply, restore, provider calls, flags or schedule.
Apply still requires the runtime backup gate, production controls and separate human Production approval.
This local branch record is not evidence that the authorization record is already present in main or that DDL has been installed.
