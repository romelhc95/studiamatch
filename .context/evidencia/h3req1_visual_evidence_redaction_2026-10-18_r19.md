# Evidencia visual sanitizada del paquete público — R19

**Estado:** derivados locales preparados; no se ha publicado R19.
**Base histórica:** snapshot R18 `0d7c89dccffd1146b6cc669d4994787e9b78b533`, preservado sin cambios. R19 se construye como rama nueva desde `4eb4d877a50b012bb630a129bd0c74482c33be9c`; no lleva el historial de originales como padre.

## Revisión y tratamiento

El manifiesto R18 seleccionó 48 archivos visuales: 46 PNG y 2 WEBM, con 31 contenidos originales distintos (29 PNG y 2 videos). Los 46 paths PNG están enumerados individualmente en el manifiesto R19 y corresponden a evidencia de onboarding y UAT pública/admin. La captura PNG que GitHub rechazó mostraba una tabla administrativa con identificadores de prueba; no se conservan ni describen aquí sus campos. Como no hay OCR local disponible para revisar de forma segura los textos de todas las capturas, no se publica ningún píxel original: las 46 rutas se sustituyen por un derivado uniforme y opaco. Los dos WEBM tampoco se publican ni se reproducen; sus originales y hashes permanecen en R18 y Syncthing. Los derivados no prueban visualmente un PASS.

Los dos videos no se cargaron ni se analizaron cuadro a cuadro: se excluyen del árbol R19. Sus originales siguen disponibles en el snapshot R18 y en el checkout local fuente; las referencias públicas de los tres documentos afectados apuntan a esta nota y conservan el identificador/hash histórico. No se ha reintentado la carga del PNG rechazado ni de ningún original visual.

El derivado público final es un PNG opaco de 6.295 bytes y 1341×1173, de color RGB uniforme `#E5E5E5`, SHA-256 `36d54261e626cb158dd592a22bbc6fec10f2d0b32b64dbb6f67524e1943a455e`. Solo contiene los chunks PNG estándar `IHDR`, `IDAT` e `IEND`; no contiene metadatos adicionales. Se inspeccionaron los píxeles decodificados y las 46 rutas comparten el mismo hash. Los 48 originales siguen presentes en Syncthing y R18, con 0 faltantes y 0 hashes distintos del inventario histórico. No se modificaron esos checkouts.

## Inventario local de originales

Las huellas siguientes identifican los archivos seleccionados en el snapshot local R18; no incluyen ni reproducen sus contenidos. La tabla existe para demostrar qué rutas se sustituyeron o excluyeron. No significa que los originales estén en el paquete público.

| Ruta original local | SHA-256 original | Bytes |
|---|---|---|
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/failed-r170/H3-UAT-002-desktop.png` | `37b2d259e799bb0312af870784ba76c87e5a7a49cc01f70dc2d088b2a4644a51` | 56060 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/failed-r170/H3-UAT-002-mobile.png` | `9e67e793bf97652a53acedbc09972add370d44cc4d0855c4a4f01253e9656f5f` | 41451 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/failed-r170/H3-UAT-002-tablet.png` | `c0499571e22eacdba7ac1cb55230609d6664770629e58b8a91d20b226c6d0e87` | 51751 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/failed-r170/H3-UAT-003-desktop.png` | `37b2d259e799bb0312af870784ba76c87e5a7a49cc01f70dc2d088b2a4644a51` | 56060 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/failed-r170/H3-UAT-003-mobile.png` | `9e67e793bf97652a53acedbc09972add370d44cc4d0855c4a4f01253e9656f5f` | 41451 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/failed-r170/H3-UAT-003-tablet.png` | `c0499571e22eacdba7ac1cb55230609d6664770629e58b8a91d20b226c6d0e87` | 51751 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r171/H3-UAT-002-desktop.png` | `1cfaff4f42583a20b04d52eb1354e077c51a3a5692fcc2d92133d6bc37b5b5b5` | 316765 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r171/H3-UAT-002-mobile.png` | `b096ceb4f0c56b8e50dd27da923d651653d5dcb53c5303e78e512b24fc47806a` | 281710 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r171/H3-UAT-002-tablet.png` | `9ba5f1067db7a327b9be63ca26d572649137e816996eb3df7a704e09ef4ace48` | 308581 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r171/H3-UAT-003-desktop.png` | `bf513678cce2f6712643e3ace8eeb933b6afc382e85e089c38a9dba84c51680f` | 321797 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r171/H3-UAT-003-mobile.png` | `30972473f0e80bb24f33cb060b5caef6ea31a68f7e55bf5cb045b1165a89c555` | 289683 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r171/H3-UAT-003-tablet.png` | `6d1bc7fbbe4f874554632e4b771b644526895fe3b24b59bb348cf83aaccd282c` | 314109 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r172/H3-UAT-002-desktop.png` | `1cfaff4f42583a20b04d52eb1354e077c51a3a5692fcc2d92133d6bc37b5b5b5` | 316765 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r172/H3-UAT-002-mobile.png` | `b096ceb4f0c56b8e50dd27da923d651653d5dcb53c5303e78e512b24fc47806a` | 281710 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r172/H3-UAT-002-tablet.png` | `9ba5f1067db7a327b9be63ca26d572649137e816996eb3df7a704e09ef4ace48` | 308581 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r172/H3-UAT-003-desktop.png` | `bf513678cce2f6712643e3ace8eeb933b6afc382e85e089c38a9dba84c51680f` | 321797 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r172/H3-UAT-003-mobile.png` | `30972473f0e80bb24f33cb060b5caef6ea31a68f7e55bf5cb045b1165a89c555` | 289683 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r172/H3-UAT-003-tablet.png` | `6d1bc7fbbe4f874554632e4b771b644526895fe3b24b59bb348cf83aaccd282c` | 314109 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r173/H3-UAT-002-desktop.png` | `1cfaff4f42583a20b04d52eb1354e077c51a3a5692fcc2d92133d6bc37b5b5b5` | 316765 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r173/H3-UAT-002-mobile.png` | `b096ceb4f0c56b8e50dd27da923d651653d5dcb53c5303e78e512b24fc47806a` | 281710 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r173/H3-UAT-002-tablet.png` | `9ba5f1067db7a327b9be63ca26d572649137e816996eb3df7a704e09ef4ace48` | 308581 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r173/H3-UAT-003-desktop.png` | `bf513678cce2f6712643e3ace8eeb933b6afc382e85e089c38a9dba84c51680f` | 321797 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r173/H3-UAT-003-mobile.png` | `30972473f0e80bb24f33cb060b5caef6ea31a68f7e55bf5cb045b1165a89c555` | 289683 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/r173/H3-UAT-003-tablet.png` | `6d1bc7fbbe4f874554632e4b771b644526895fe3b24b59bb348cf83aaccd282c` | 314109 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-001.png` | `f796802572ad4d90b47e449db6c99c4165dfe6275530edeea26b77520f6df4bd` | 68096 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-002.png` | `6fbf32e6f50e8e2ee98bc07bb13632b58d04b31a5ec6b1c82627e55958451f64` | 65666 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-003.png` | `a3d81942eeb32ce313de289600a853ab5f9008fc4d7a35aa84baf2549837b5b8` | 13535 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-004.png` | `a3d81942eeb32ce313de289600a853ab5f9008fc4d7a35aa84baf2549837b5b8` | 13535 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-005.png` | `79c0a0da98fa5edd1917f4af2ebd29c400b2ebeb574a1d650142f60918035b11` | 57183 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-007.png` | `b98a2d626ee05a84badb0e3f63664ce48de025742a25f15d03f400dcf76ce886` | 81120 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-008.png` | `95451e52018c36fb287de8d4d3c11b4802d9a27d54e83cc517e8ea2abdfae437` | 57008 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-009.png` | `e9266e65b03ce3a74590a27f22e97ab7a334ebae407f34409e252bee3c698442` | 197389 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-012.png` | `a3d81942eeb32ce313de289600a853ab5f9008fc4d7a35aa84baf2549837b5b8` | 13535 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-013.png` | `49d05852365b174fa6d1aacf690118243082694d3379cdcd9ddf20be3f3f4d7b` | 15420 |
| `.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/videos/onboarding-user-flow.webm` | `d3bcc728cdac293c85a591edaf34d2b819038a3ba131cdb94ffbc1a917d142d3` | 366847 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-compare-and-pipeline-r70/H3-UAT-049-desktop.png` | `e7015ade5023fe6b255c6b97282c18ef2595c7462db15a84a96170411894d580` | 107265 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-compare-and-pipeline-r70/H3-UAT-049-desktop.webm` | `196acd796c6aa25499c20b12977cb5dfb7641293825275dbada7b3d12dfb2452` | 2086158 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-compare-and-pipeline-r70/H3-UAT-049-mobile.png` | `4b400c07f54d7112b552271beeaf91b068aaeb1887b1a8931c56d1dd4e12722d` | 90182 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-compare-and-pipeline-r70/H3-UAT-049-tablet.png` | `16c18681f8456689c6177b7845791e5f44b47b9a85ef2b03e38e9dea9970aebd` | 101052 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-compare-and-pipeline-r70/H3-UAT-064-desktop.png` | `0fb3aab9b10d4550643e39bab36d96f37fc90117be1cd53ea4328f36d5a1f550` | 140640 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-compare-and-pipeline-r70/H3-UAT-064-mobile.png` | `43f0000b492297706b07df630920da6139812f800351e61a75ea751ae17723bc` | 126609 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-compare-and-pipeline-r70/H3-UAT-064-tablet.png` | `44039c0d3ec40cab98fece84f75cdff4bcb7f5d2a99af69387121ce295b77c94` | 122980 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-desktop.png` | `db4243b8e91a92ac63d24287f60c402e103979877f42a4ba018abee6adce5296` | 141590 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-mobile.png` | `4a969f86e144c40fa8de7a28938fcd9b86464bf5a168720ea1427754caee87fb` | 83456 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-tablet.png` | `38c4f493c693451a79e387eafcbd57cb81ce25d4b6a6ed26af21eb7c3b1654e3` | 106901 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/H3-UAT-065-desktop.png` | `838d8b9536d7eb17713b64948f1db5b57fe5b25696c0b959d8ef2aba3b3d9513` | 130938 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/H3-UAT-065-mobile.png` | `76e119a1c11483c8638a1a709ddcacfc7e1583c7a393498ad5302fd5004bece3` | 112911 |
| `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/H3-UAT-065-tablet.png` | `507c04c83243e2d24f5fc9ef52ef5c65b1fc291119e0134c0b3a008d0417b15b` | 121624 |
