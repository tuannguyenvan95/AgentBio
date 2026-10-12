# 🧬 AgentBio: Autonomous Synthetic Biology Protocol & DNA Sequence Safety Escrow

> **Track:** DeSci (Decentralized Science) / Biosecurity / Subjective Consensus  
> **Target Network:** GenLayer Studionet (Chain ID: `61999` / `0xF1EF`, RPC: `https://studio.genlayer.com/api`)  
> **Authoritative Intelligent Contract:** `0x393Dcc177aC202e2ccD01ec76303E557bfc4d43A`  
> **Live Production dApp:** [https://agentbio.vercel.app](https://agentbio.vercel.app)  
> **GitHub Repository:** [https://github.com/tuannguyenvan95/AgentBio](https://github.com/tuannguyenvan95/AgentBio)  
> **Hackathon Target:** Agent Tank Hackathon — Track: DeSci & Subjective Consensus  
> **Brand & Design Concept:** Genomic Cleanroom / Bio-Foundry Console (Light sterile slate `#F1F5F9`, Pure White `#FFFFFF`, Bio-Green `#059669`, Nucleic Purple `#7C3AED`, Biohazard Orange `#EA580C`)

---

## 🔬 1. Bối cảnh & Tư tưởng "Độc Bản" (Zero Duplication)

Trong kỷ nguyên AI thiết kế protein và sinh học tổng hợp phi tập trung (DeSci), các nhà khoa học, phòng thí nghiệm tự động trên mây (**Cloud Bio-Labs**) hoặc các **AI Agent** tự hành đặt hàng tổng hợp chuỗi gen / plasmid (DNA/RNA sequences) qua mạng từ các nhà máy in sinh học (**DNA Foundry / Synthesis Providers**).

### Vấn đề nan giải
1. **Bên đặt hàng (Bio-Researcher / Ordering Agent):** Muốn thuê tổng hợp chuỗi protein hoặc enzyme trị liệu, nhưng sợ bên in sinh học giao sản phẩm đột biến sai trình tự, không đúng folding/chức năng, hoặc đơn vị sản xuất lén hủy đơn giữ cọc.
2. **Bên in sinh học (DNA Foundry):** Sợ khách hàng gửi các chuỗi gen chứa độc tố sinh học nguy hiểm hoặc mầm bệnh bị cấm (**Biosecurity Dual-Use Pathogens / Select Agents**) bị che giấu dưới dạng đột biến giả để né tránh bộ lọc lỏng lẻo.
3. **Sự bất lực của Smart Contract EVM truyền thống:**
   - Solidity không thể đọc hiểu chuỗi ký tự nucleotide (A, T, C, G) hay chuỗi axit amin (định dạng FASTA / GenBank).
   - Không thể truy vấn cơ sở dữ liệu mầm bệnh NCBI / UniProt live trên web.
   - Không thể thẩm định xem một cấu trúc protein có tiềm ẩn nguy cơ vũ khí sinh học hay vi phạm chuẩn mực DeSci quốc tế hay không.

### Giải pháp đột phá từ AgentBio trên GenLayer
AgentBio tận dụng năng lực **Intelligent Contract (GenVM)** của GenLayer:
- **Cào live kết quả giải trình tự QC** trực tiếp on-chain qua `gl.nondet.web.render`.
- **Hội đồng Thẩm định An toàn Sinh học AI On-Chain (International Biosecurity & Sequence QC Jury):** Bồi thẩm đoàn AI thực thi mô hình ngôn ngữ lớn đánh giá độ khớp chuỗi (Sequence Fidelity ≥ 80%) và sàng lọc mầm bệnh nguy hiểm.
- **Đồng thuận chủ quan (Subjective Consensus):** Xác minh tính tương đương ngữ nghĩa qua `validator_fn` so sánh Semantic Verdict, Evidence SHA-256 Hash, và sai số điểm tương đồng.
- **Mô hình kinh tế tự bảo vệ (Self-Enforcing Biosecurity):**
  - **BIO_SYNTHESIS_VERIFIED:** 100% tiền giải ngân cho DNA Foundry.
  - **BIOHAZARD_BLOCKED:** Toàn bộ tiền cọc của khách hàng bị **tịch thu chuyển vào Quỹ bảo an sinh học DeSci** (phạt nặng bên cố tình in mầm bệnh độc hại).
  - **SEQUENCE_DEFECTIVE:** 100% tiền hoàn trả cho khách hàng (bảo vệ nhà nghiên cứu trước nhà máy in cẩu thả).

---

## 🏛️ 2. Kiến trúc Intelligent Contract (`contracts/contract.py`)

Contract được xây dựng theo chuẩn mực cao nhất của GenLayer GenVM:
- **Magic Pragma:** `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }`
- **GenVM Storage Types:** `TreeMap[u64, BioOrder]`, `DynArray[u64]`, `bigint`, `u8`, `u32`, `u64`, `u256`.
- **Security Canary Token:** `CANARY_AGENT_BIO_SAFETY_V1` ngăn chặn prompt injection.
- **Authorized Foundry Participation:** Sổ đăng bạ Foundry ủy quyền (`authorized_foundries`, `foundry_lab_ids`) ngăn chặn hoàn toàn ví lạ tùy tiện nhận đơn; hỗ trợ chỉ định đích danh (`target_foundry`).
- **Immutable Commissioned Specifications:** Khóa mã băm SHA-256 (`spec_evidence_hash`) bất biến tại thời điểm đặt đơn, loại bỏ rủi ro tráo đổi nội dung URL.
- **Independently Authenticated QC:** Xác thực chứng chỉ phòng lab (`lab_attestation_id`) và mã băm kết quả giải trình tự (`qc_evidence_hash`).
- **Defensible Biosecurity & Appellate Tribunal:** Tòa án phúc thẩm cho phép đảo ngược phán quyết nhầm mầm bệnh (`APPEAL_BIOHAZARD_OVERTURNED_BENIGN`), bảo vệ quyền lợi chính đáng của nhà nghiên cứu không bị tịch thu tài sản oan.
- **Trusted Timing Path:** Thời gian thực thi dẫn xuất trực tiếp từ GenVM message datetime, loại bỏ hoàn toàn sai số đồng hồ máy tính cục bộ.
- **Immediate Constructor Binding:** Quyền quản trị Protocol và Quỹ dự trữ được gán trực tiếp cho Deployer ngay trong hàm dựng `__init__`.
- **Native Transfers:** `gl.get_contract_at(recipient).emit_transfer(value=u256(amount))`.

### Vòng đời trạng thái của Đơn hàng Sinh học (BioOrder Status Lifecycle):
```mermaid
stateDiagram-v2
    [*] --> STATUS_ORDER_OPEN: order_synthesis (Lock Escrow & Commit Spec Hash)
    STATUS_ORDER_OPEN --> STATUS_IN_SYNTHESIS: accept_synthesis_agreement (Authorized Foundry Binds)
    STATUS_ORDER_OPEN --> STATUS_CANCELLED: cancel_or_reclaim (Expired)
    
    STATUS_IN_SYNTHESIS --> STATUS_AWAITING_PAYOUT: adjudicate_biosecurity_and_qc (AI Jury Consensus & Hash Verification)
    
    STATUS_AWAITING_PAYOUT --> STATUS_DISPUTED: appeal_verdict (10% Staked Bond within Cooling-Off)
    
    STATUS_AWAITING_PAYOUT --> STATUS_VERIFIED_PAID: finalize_settlement (Fidelity >= 80% & Safe)
    STATUS_AWAITING_PAYOUT --> STATUS_BIOHAZARD_SLASHED: finalize_settlement (Pathogen Detected -> Slashed to Reserve)
    STATUS_AWAITING_PAYOUT --> STATUS_DEFECTIVE_REFUNDED: finalize_settlement (Mutated / Fidelity < 80% -> Refunded)
    
    STATUS_DISPUTED --> STATUS_DEFECTIVE_REFUNDED: adjudicate_appeal (Biohazard Overturned Benign / Defect Proven)
    STATUS_DISPUTED --> STATUS_VERIFIED_PAID: adjudicate_appeal (Foundry Upheld Verified)
    STATUS_DISPUTED --> STATUS_BIOHAZARD_SLASHED: adjudicate_appeal (Biohazard Confirmed)
```

---

## 🧪 3. Bảng Kiểm Thử Hợp Đồng (`tests/`) & Bằng Chứng Giao Dịch Live StudioNet

Tất cả **43 bài test** trong test suites được kiểm thử tự động và vượt qua **100%**:
- `tests/test_adversarial_and_consensus.py` (3 tests): Validator fidelity threshold disagreement across 80%, offline/unavailable evidence aborts without forfeiture, on-chain financial multi-wallet settlement.
- `tests/test_agent_bio.py` (4 tests): Genuine content commitments, retrieval failure aborts without penalty, independent 80% fidelity enforcement, accredited appeals.
- `tests/test_agentbio.py` (13 tests): Cú pháp GenVM, storage struct, canary token, validator consensus, và behavioral simulation (settlement, cooling-off window, refund, Sybil defence).
- `tests/test_biosecurity_evidence_and_appeal.py` (23 tests): Bao gồm các test đối kháng (Adversarial E2E Tests) kiểm tra bảo vệ Foundry chỉ định, chống bypass, cam kết bằng chứng băm kép.

Để chạy toàn bộ kiểm thử:
```bash
pytest tests/ -v
```

### ⛓️ Bảng Đối Chiếu Bằng Chứng Giao Dịch Thực Tế Trên GenLayer StudioNet:
> **Authoritative Contract Address:** `0x393Dcc177aC202e2ccD01ec76303E557bfc4d43A`  
> **Deployer / Researcher Account:** `0xF34587A45C397281Ef6BDd839d4A1de2DEe393ad`  
> **Accredited Foundry Account:** `0x2f166C507c7fbd7885999207058a4BA6A2E49BaC`  

| Bước Nghiệp Vụ | Tên Hàm Giao Dịch | Transaction Hash Trên StudioNet | Kết Quả Thực Thi |
| :--- | :--- | :--- | :--- |
| **0. Contract Deployment** | `Contract.__init__` | `0x879d3bcfa3c95990e1386ac0d5ae8e5556373012c03c217f4249a43fa76bf5c6` | Hợp đồng khởi tạo thành công, owner & reserve gán ngay trong constructor |
| **1. Set Cooling-Off** | `set_cooling_off_seconds(5)` | `0x720fb34839f75eb787c6b76c502551b6ccbe4a347ee54ee0169b533157c23a39` | Cấu hình cửa sổ khiếu nại linh hoạt cho phép nghiệm thu nhanh |
| **2. Register Foundry** | `register_foundry(...)` | `0xd895baf10ad4491877f5671e80899775626bb4016b98ed829708ce025d0ff2c6` | Cấp chứng nhận `ISO-17025-TWIST-BIOSYNTH-01` cho ví Foundry |
| **3. Order Synthesis #1** | `order_synthesis_designated(...)` | `0xd2c8d8933e73f80b01d2e117b0fed3059e6fbe534183b2bd88fdcd927e8e6af0` | Khóa `0.015 GEN` ký quỹ + Gắn mã băm nội dung tài liệu 64-hex SHA-256 (`b78e...74dd`) |
| **4. Accept Agreement** | `accept_synthesis_agreement(1)` | `0x8bda1dd389e9b9479f05559653365b20713c31c8d1332e5132848f930330b661` | Ví Foundry chấp thuận điều khoản hợp đồng song phương |
| **5. Submit QC Proof** | `submit_synthesis_proof(1, ...)` | `0x6b3a23f72d293ee804c71e9c9e9226d28effafe737a42c28588087176ff118e0` | Nộp chứng nhận giải trình tự + Cam kết mã băm QC 64-hex SHA-256 |
| **6. AI Jury Adjudication** | `adjudicate_biosecurity_and_qc(1)` | `0xe7e47d7c477bad84d0da494df34396f47d7dd16671b6329ea0003096e605616e` | Bồi thẩm đoàn AI đồng thuận: `BIO_SYNTHESIS_VERIFIED`, Độ khớp 100%, Tin cậy 100% |
| **7. Clear Cooling-Off** | `set_order_cooling_off(1, 0)` | `0x66b45ca529540007b48b0d36a14d0c8af81c1599488a29b15e607eb119779a6a` | Cửa sổ làm nguội kết thúc, mở khóa giải ngân tài chính |
| **8. Finalize Settlement** | `finalize_settlement(1)` | `0xabb2b6078547c37ef33b5901dff10569b2dac67fc73884580509a4c9bb61136d` | Nghiệm thu tài chính on-chain: Trạng thái cập nhật `STATUS_VERIFIED_PAID`, giải ngân Escrow |
| **9. Order Synthesis #2** | `order_synthesis(...)` | `0x82c68b3eb31f6b9eff814c008006fa4aac18aa7000fd575086f38f8d201e8f14` | Mở đơn hàng sinh học tự do thứ 2 (CRISPR-Cas9 guide RNA), khóa `0.01 GEN` |

---

## 🎨 4. Giao Diện Người Dùng (Genomic Cleanroom / Bio-Foundry Console)

- **Tone màu chủ đạo:** Nền trắng ngọc trai lạnh `#F1F5F9`, Card bề mặt kính phòng thí nghiệm `#FFFFFF` viền thép `#CBD5E1`.
- **Hệ màu nhấn:**
  - **Bio-Green (`#059669`):** Chuỗi gen đạt chuẩn tinh sạch & an toàn sinh học.
  - **Nucleic Purple (`#7C3AED`):** Đơn hàng đang được nhà máy in và giải trình tự QC.
  - **Biohazard Orange (`#EA580C`):** Báo động phát hiện mầm bệnh độc hại bị phong tỏa.
- **Typography:** Display font Space Grotesk / Plus Jakarta Sans, mã nucleotide và hash hiển thị bằng JetBrains Mono.
- **Tính năng giao diện:**
  - Kết nối ví MetaMask tự động chuyển mạng GenLayer Studionet (Chain ID: 61999).
  - Thanh thống kê Real-time: Tổng Escrow khóa, Số đơn đã nghiệm thu, Mầm bệnh đã chặn.
  - Bộ lọc trạng thái đa năng (All, Open, In Synthesis, Cooling-off, Verified, Biohazard, Defective, Disputed).
  - Modal **Commission DNA Synthesis** có sẵn mẫu chuẩn DeSci (Kháng thể đơn dòng, Enzyme phân hủy nhựa PETase, Cảm biến sinh học Luciferase).
  - Modal **Foundry QC Portal** nộp link Sanger/NGS sequencing.
  - Modal **Biosecurity & Fidelity Forensic Dossier** hiển thị thước đo độ khớp, bằng chứng SHA-256 hash và lập luận của AI.

---

## 🚀 5. Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### Khởi chạy Frontend:
```bash
cd frontend
npm install
npm run dev
```
Ứng dụng sẽ chạy tại `http://localhost:3000`.

### Cấu hình Mạng GenLayer Studionet:
- **Network Name:** GenLayer Studionet
- **RPC URL:** `https://studio.genlayer.com/api`
- **Chain ID:** `61999` (Hex: `0xF1EF` / `0xf22f`)
- **Currency Symbol:** `GEN`
- **GenLayer Studio:** [https://studio.genlayer.com](https://studio.genlayer.com)

---

## 🏆 6. Điểm Nhấn "Ăn Điểm Tuyệt Đối" Khi Thuyết Trình Pitching

1. **Tiên phong thị trường DeSci & An toàn Sinh học (First-Ever Web3 Biosecurity Escrow):** Lần đầu tiên trên thế giới có một smart contract có khả năng ngăn chặn việc lợi dụng mạng phi tập trung để in lén các mầm bệnh nguy hiểm.
2. **Khác biệt hoàn toàn với EVM / Solidity:** Solidity hoàn toàn mù tịt trước các file FASTA, không thể phân tích chuỗi codon của DNA, và không thể tra cứu mầm bệnh nguy hiểm live trên mạng.
3. **Mô hình kinh tế tự bảo vệ (Self-Enforcing Biosecurity):** Nhà nghiên cứu chân chính được bảo đảm chất lượng tổng hợp; kẻ gian cố tình in vũ khí sinh học bị trừng phạt tịch thu 100% tiền cọc đưa vào Quỹ phòng vệ sinh học DeSci.
