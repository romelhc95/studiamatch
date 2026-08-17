# F10.9 G5 - PR P Trusted Boundary Registration Probe

Estado: `PREPARED_FOR_FUTURE_PR_P_ONLY`.

Este archivo existe para que el futuro PR P tenga un delta exacto y minimo:
modificar este documento como un unico commit directo desde la base protegida. El
perfil `PR_P_DEFAULT_BRANCH_REGISTRATION_PROBE` debe rechazar forks,
modificaciones a `.github/workflows/**`, modificaciones a
`scripts/security/f109_trusted_boundary_bootstrap.py`, multiples commits,
renames, mode drift y cualquier path adicional.

El check esperado para ese futuro PR es `F10.9 Trusted Boundary v1`. PR O no pudo
autoatestiguarse porque fue el bootstrap humano que registra el workflow en la
rama por defecto; PR Q conserva este perfil exacto y endurece el check permanente
antes de la promocion selectiva posterior, preparada y no ejecutada aqui.
