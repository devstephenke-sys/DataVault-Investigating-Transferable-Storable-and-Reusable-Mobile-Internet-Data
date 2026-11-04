# Technical Report: Operator-Controlled Quota Transfer and Reservation for DataVault

**Date:** November 4, 2026
**Research Focus:** 3GPP Charging Architecture and Operator API Exposure for Quota Transfer
**Target Application:** DataVault - Independent Gateway with Quota Redemption Capability

---

## Executive Summary

This report investigates the technical feasibility of exposing operator-controlled quota transfer and reservation APIs through 3GPP charging architecture. The research confirms that 3GPP standards provide robust mechanisms for quota reservation, inter-operator quota transfer (B2B charging), and network exposure through standardized APIs. The findings validate the "Carrier-integrated DataVault" research direction as the most viable path forward.

**Key Finding:** 3GPP TS 32.240 and related specifications define a complete B2B charging architecture that enables quota transfer between operators (B-CHF and C-CHF), which can be exposed to third parties via Network Exposure Function (NEF) and Common API Framework (CAPIF).

---

## 1. 3GPP Charging Architecture Overview

### 1.1 Core Specifications

**Primary References:**
- **3GPP TS 32.240** - Charging Architecture and Principles (Release 18+)
- **3GPP TS 32.290** - Service Based Interface for Charging
- **3GPP TS 32.291** - Nchf Converged Charging Service
- **3GPP TS 32.254** - Exposure Function Northbound APIs Charging
- **3GPP TS 23.501** - 5G System Architecture (NEF functionality)

### 1.2 Online Charging and Quota Reservation

**Quota Reservation Mechanism (TS 32.240 Section 5.1):**

Online charging is a process where:
1. Authorization for network resource usage must be obtained **before** resource usage occurs
2. The Online Charging System (OCS) or Converged Charging System (CCS) grants authorization upon request
3. Authorization may be limited in scope (e.g., volume of data or duration)
4. Authorization must be renewed as long as usage persists

**Unit Reservation:**
- The OCS/CCS cannot a priori know the amount of resources the end user may consume
- A certain amount of (monetary or non-monetary) units is **blocked or reserved** on the subscriber's account
- Permission to use resources matching the unit reservation is returned to the network
- When granted units are used, the network must send a new request for unit allocation
- Used units must be returned to OCS/CCS so over-reserved amounts can be re-credited

**Credit-Control Flow:**
```
UE → Network Function (CTF) → OCS/CCS (CHF)
   ← Authorization     ← Quota Grant
```

### 1.3 Charging Function (CHF) Architecture

**Components (TS 32.240 Section 4.3.3.2.1):**
- **Online Charging Function (OCF)** - Quota management under Credit-Control terminology
- **Charging Data Function (CDF)** - CDR generation for charging events
- **Charging Gateway Function (CGF)** - CDR file creation and transfer to billing domain

**CHF Capabilities (TS 32.291):**
- Quota allocation and re-authorization triggers
- Notification when rating conditions are affected
- Receiving service usage reports from NF Service Consumer
- CDR generation

---

## 2. B2B Charging and Inter-Operator Quota Transfer

### 2.1 B2B Charging Architecture

**Business CHF (B-CHF) and Consumer CHF (C-CHF) Model (TS 32.240 Section G.3):**

The B2B charging architecture supports:
- **B-CHF only interaction:** Quota requested and granted directly between CTF and B-CHF
- **B-CHF via C-CHF interaction:** Quota requested and granted between CTF and B-CHF via C-CHF

**Key Capabilities:**
```
CTF → B-CHF (request quota)
   ← (grant quota)

OR

CTF → C-CHF → B-CHF (request quota)
   ← ← (forward and re-allocate quota)
```

### 2.2 Quota Management for Inter-CHF (TS 32.290 Section 5.4.8.2)

**Consumer CHF to Producer CHF Communication:**

Upon receiving Charging Data Request [Initial/Update] from NF Consumer (CTF):
1. Consumer CHF may send request to producer CHF **with or without** quota amount
2. Consumer CHF may send request with quota amount **larger** than from NF Consumer
3. Consumer CHF may allocate quota based on **previous granted quota** from producer CHF

**Quota Forwarding:**
- When receiving quota from producer CHF, consumer CHF may send quota to NF Consumer with **same or less** amount as granted by producer CHF

**Supported Scenarios:**
- 5G data connectivity charging in local breakout roaming
- 5G connection and mobility charging
- MVNO charging scenarios (A-CHF architecture)

### 2.3 MVNO and Additional Actor Support (TS 32.255)

**N47 Reference Point:**
- Used by A-CHF (Additional Actor CHF, e.g., MVNO) to perform retail charging
- Operator-specific implementation allowed
- SMF and CHF owned by MNO determine which architecture to use based on operator agreement

**This is directly relevant to DataVault as an independent gateway that could act as an "additional actor" with its own CHF or integrate via operator's CHF.**

---

## 3. Network Exposure Function (NEF) and API Exposure

### 3.1 NEF Functionality (TS 23.501 Section 6.2.5.0)

**Core Capabilities:**
- Secure exposure of NF capabilities and events to 3rd parties, Application Functions, Edge Computing
- Charging data collection and support of charging interfaces
- Translation of information between AF and internal 3GPP NFs
- Monitoring of UE-related events for external exposure

**Exposed Services Include:**
- Voice
- Data connectivity
- **Charging**
- Subscriber data
- IoT capabilities

### 3.2 Converged Charging Support for NEF

**Oracle NEF User Guide:**
- NEF can engage in converged charging through interaction with CHF NF using Nchf
- Enables credit control, accounting, billing, and statistics
- Facilitates charging for northbound API invocation

**TS 28.816 Section 4.3.3 - CP Data Transfer Charging with NEF:**
- Converged charging performed by NEF interacting with CHF using Nchf service
- Charging requirements for northbound API specified in TS 32.254

### 3.3 Northbound API Charging (TS 32.254)

**Specification Scope:**
- Offline, online, and converged charging description for Northbound APIs
- Based on T8 reference point (SCEF to SCS/AS) and NEF (TS 23.501)
- Maps common 3GPP charging architecture onto Northbound APIs
- Specifies structure and content of CDRs for offline charging

**Relevance to DataVault:**
- Operators can expose charging-related APIs to third parties
- API invocations can be charged and quota-controlled
- Enables monetization of network capabilities through API exposure

---

## 4. Common API Framework (CAPIF)

### 4.1 CAPIF Overview

**Purpose (TS 23.222):**
- Unified framework for securely discovering, accessing, and utilizing 3GPP network APIs
- Controls access of service API by API invoker based on policy or usage limits
- Authorization can be revoked when usage limits exceeded

### 4.2 CAPIF Components

**Core Functions:**
- **API Management Function (AMF)** - Administrative capabilities, auditing, onboarding
- **API Publishing Function (APF)** - Publication of service APIs for discovery
- **API Exposing Function (AEF)** - Direct communication entry point, authorization validation
- **Common Core Function (CCF)** - Central coordination

### 4.3 Charging Integration (Rel-19)

**From 3GPP Charging Enhancements Rel-19:**
- Integration with CAPIF brings charging into network exposure
- Charging hooks added to CAPIF
- Operators can bill Service API Providers for management (e.g., publishing service APIs)
- Operators can bill Service API invokers for API discovery and usage
- Enhances monetization of partnerships where network capabilities are consumed by third parties

### 4.4 Usage Limits and Authorization

**TS 23.222 Section 8.23.1:**
- CAPIF controls API access based on policy or usage limits
- When usage limits exceeded, authorization is revoked
- Decision to revoke may be triggered by AEF or CAPIF core function
- In RNAA scenarios, decision may be initiated by CAPIF core function

**This is critical for DataVault - quota limits can be enforced at the API layer.**

---

## 5. Research Directions Assessment

### 5.1 Local Packet Storage

**Definition:** Stores traffic locally without creating new internet access

**Assessment:**
- Does not align with 3GPP charging architecture
- Not addressed in specifications
- Limited regulatory pathway

**Verdict:** Not viable for operator-controlled quota transfer

### 5.2 Portable Subscriber Entitlement

**Definition:** Preserves operator-authorised right to consume data across devices

**Assessment:**
- Partially supported through IMSI/IMPI mechanisms
- Could leverage 3GPP subscription management
- Requires deep integration with HSS/UDM
- Limited precedent for cross-device quota portability

**Verdict:** Possible but complex; requires operator-specific implementation

### 5.3 Carrier-Integrated DataVault (RECOMMENDED)

**Definition:** Allows an independent device to redeem a previously allocated quota

**Technical Pathway:**

**Option A: Direct CHF Integration**
```
DataVault → Operator's CHF (via secured API)
         ← Quota allocation
```
- DataVault acts as an NF Consumer (CTF)
- Requests quota directly from operator's CHF
- Operator exposes Nchf_ConvergedCharging API via NEF/CAPIF
- Quota is reserved on subscriber's account
- DataVault enforces quota locally

**Option B: B2B CHF Model**
```
DataVault (C-CHF) → Operator's B-CHF
                 ← Quota delegation
```
- DataVault operates its own Consumer CHF
- Establishes B2B relationship with operator's Business CHF
- Uses N107 reference point for inter-CHF communication
- Operator delegates quota to DataVault's CHF
- DataVault re-allocates quota to end devices

**Option C: MVNO-like Model**
```
DataVault (A-CHF) → Operator's CHF (via N47)
                ← Retail charging quota
```
- DataVault acts as Additional Actor with own CHF
- Uses N47 reference point (operator-specific implementation)
- Similar to MVNO arrangement
- Requires operator agreement

**Verdict:** **STRONGLY RECOMMENDED** - Fully supported by 3GPP standards with multiple implementation options

---

## 6. Kenya Regulatory Framework Analysis

### 6.1 Regulatory Authority

**Communications Authority of Kenya (CA):**
- Established by Kenya Information and Communications Act, 1998
- Responsible for ICT sector regulation
- Licenses telecommunications operators and service providers
- Enforces licence conditions and regulations

### 6.2 Licensing Framework

**Unified Licensing Framework (ULF):**
- Technology and service neutrality principles
- Simplifies market entry by minimizing regulatory requirements
- Based on 3 categories:
  1. Network Facility Providers (infrastructure)
  2. Application Service Providers (value-added services)
  3. Content Service Providers (content to end users)

**Relevant Licences for DataVault:**
- **Network Facility Provider:** Not required (DataVault doesn't own network infrastructure)
- **Application Service Provider:** Potentially applicable if providing value-added data services
- **Content Service Provider:** Not applicable (not delivering content to end users)

### 6.3 Data Centre Licensing

**Current Status (CA Consultation Document):**
- Data centres established in two ways:
  1. Fully-fledged with space, power, connectivity, computing
  2. Colocation facilities (space, power, connectivity only)
- Holders of certain licences permitted to establish commercial data centres without additional licence

**Relevance:** DataVault would likely operate from a data centre, which may be eligible under existing licence framework.

### 6.4 Market Structure Considerations

**From Telecommunications Market Structure Review:**
- Authority reviews sector continuously to foster competition
- Guards against anti-competitive behaviour
- Encourages private investment in telecommunications sector

**Implication:** DataVault must ensure its model does not violate competition regulations, particularly regarding inter-operator arrangements.

---

## 7. Recommended Implementation Path

### 7.1 Phase 1: Proof of Concept (Research Prototype)

**Objective:** Validate technical feasibility with single operator

**Approach:**
1. Engage with a Kenyan MNO (Safaricom, Airtel, Telkom Kenya)
2. Request API access to Nchf_ConvergedCharging via NEF
3. Implement DataVault as NF Consumer (CTF)
4. Test quota reservation and enforcement
5. Validate security and authentication

**Technical Requirements:**
- 3GPP-compliant API client
- Mutual TLS authentication
- OAuth 2.0 / OpenID Connect for API security
- Local quota enforcement engine
- Usage reporting and reconciliation

### 7.2 Phase 2: B2B Integration

**Objective:** Establish formal B2B charging relationship

**Approach:**
1. Negotiate operator agreement for inter-CHF communication
2. Implement C-CHF functionality in DataVault
3. Establish N107 reference point integration
4. Test quota delegation and re-allocation
5. Implement CDR generation and reporting

**Technical Requirements:**
- Converged CHF implementation (open-source: free5GC, Open5GS)
- Nchf service implementation
- B2B charging architecture (TS 32.240 G.3)
- Inter-operator security framework

### 7.3 Phase 3: Multi-Operator Expansion

**Objective:** Scale to multiple operators

**Approach:**
1. Integrate with additional MNOs
2. Implement quota pooling across operators
3. Develop unified API for end-user applications
4. Launch commercial service

**Technical Requirements:**
- Multi-operator quota management
- Unified authentication and authorization
- Real-time quota synchronization
- Compliance monitoring

### 7.4 Phase 4: Regulatory Compliance

**Objective:** Ensure regulatory approval

**Approach:**
1. Engage with Communications Authority of Kenya
2. Determine applicable licence category
3. Submit licensing application
4. Obtain regulatory approval
5. Launch service

**Regulatory Considerations:**
- Application Service Provider licence (if applicable)
- Data centre compliance
- Consumer protection regulations
- Interconnection agreements
- Competition compliance

---

## 8. Security Considerations

### 8.1 API Security

**Requirements:**
- Mutual TLS for all API communications
- OAuth 2.0 with client credentials for machine-to-machine auth
- API rate limiting and throttling
- Request signing and validation
- Secure credential management

### 8.2 Quota Security

**Risks (Based on P1sec Analysis):**
- CHF is an online policy enforcement point
- CHF does not observe traffic directly - trusts consumer function
- Potential for quota manipulation if consumer function compromised

**Mitigations:**
- Tamper-evident quota enforcement in DataVault
- Cryptographic signing of quota grants
- Regular reconciliation with operator CHF
- Audit logging of all quota operations
- Hardware security module (HSM) for key management

### 8.3 Inter-Operator Security

**Requirements:**
- Cross-domain authentication and authorization
- Private network interconnects (IPX or direct)
- IPsec tunnels for inter-CHF communication
- Bilateral security agreements
- Fraud detection and prevention

---

## 9. Technical Specifications Summary

### 9.1 Key 3GPP Specifications

| Specification | Title | Relevance |
|--------------|-------|-----------|
| TS 32.240 | Charging Architecture and Principles | Core charging framework, quota reservation |
| TS 32.290 | Service Based Interface for Charging | Nchf services, inter-CHF communication |
| TS 32.291 | Nchf Converged Charging Service | API operations for quota management |
| TS 32.254 | Exposure Function Northbound APIs Charging | Charging for exposed APIs |
| TS 32.255 | 5G Data Connectivity Charging | MVNO and additional actor support |
| TS 23.501 | 5G System Architecture | NEF functionality |
| TS 23.222 | Common API Framework (CAPIF) | API exposure and management |
| TS 29.222 | CAPIF Service APIs | OpenAPI specifications |
| TS 28.816 | CP Data Transfer Charging with NEF | NEF charging implementation |

### 9.2 API Interfaces

**Nchf_ConvergedCharging (TS 32.291):**
- `Nchf_ConvergedCharging_Create` - Request initial quota
- `Nchf_ConvergedCharging_Update` - Request additional quota, report usage
- `Nchf_ConvergedCharging_Release` - Release quota on session termination
- `Nchf_ConvergedCharging_Notify` - Receive re-authorization triggers

**Nchf_SpendingLimitControl:**
- Retrieve policy counter status
- Subscribe to spending limit events

**CAPIF APIs (TS 29.222):**
- `CAPIF_Discover_Service_API` - Discover available APIs
- `CAPIF_Events_API` - Subscribe to events
- `CAPIF_Logging_API_Invocation_API` - Log API invocations

---

## 10. Conclusions and Recommendations

### 10.1 Technical Feasibility

**Conclusion:** Operator-controlled quota transfer and reservation is **technically feasible** and fully supported by 3GPP standards.

**Evidence:**
- B2B charging architecture (TS 32.240 G.3) enables inter-operator quota transfer
- Quota management for inter-CHF (TS 32.290 5.4.8.2) provides delegation mechanisms
- NEF (TS 23.501) and CAPIF (TS 23.222) enable secure API exposure
- Northbound API charging (TS 32.254) enables monetization of exposed APIs
- MVNO and additional actor support (TS 32.255) provides precedents

### 10.2 Regulatory Feasibility

**Conclusion:** The Kenya regulatory framework is **accommodating** but requires engagement.

**Evidence:**
- Unified Licensing Framework based on technology neutrality
- Application Service Provider category likely applicable
- Data centre licensing provisions exist
- CA encourages private investment and innovation

**Requirement:** Early engagement with Communications Authority of Kenya is essential.

### 10.3 Recommended Path Forward

**Immediate Actions:**
1. **Develop Proof of Concept:** Implement DataVault as NF Consumer with test operator
2. **Operator Engagement:** Initiate discussions with Kenyan MNOs for API access
3. **Regulatory Engagement:** Schedule meeting with Communications Authority of Kenya
4. **Technical Architecture:** Finalize implementation approach (Option A, B, or C)
5. **Funding:** Secure funding for development and deployment

**Implementation Priority:**
1. Start with Option A (Direct CHF Integration) - lowest barrier to entry
2. Progress to Option B (B2B CHF Model) for scalability
3. Consider Option C (MVNO-like Model) for independence

### 10.4 Success Factors

**Critical Success Factors:**
1. **Operator Partnership:** Must have at least one MNO willing to expose charging APIs
2. **Regulatory Approval:** Must obtain appropriate licence from CA
3. **Security Implementation:** Must implement robust security to protect quota integrity
4. **Market Validation:** Must demonstrate clear value proposition to end users
5. **Technical Excellence:** Must ensure reliable, compliant implementation

### 10.5 Next Steps

**Research Phase (Months 1-3):**
- Complete technical deep-dive into chosen specifications
- Develop technical architecture document
- Identify open-source implementations (free5GC, Open5GS)
- Engage legal counsel for regulatory review

**Development Phase (Months 4-9):**
- Develop Proof of Concept
- Secure test environment with operator
- Implement and test quota reservation
- Validate security and authentication

**Pilot Phase (Months 10-12):**
- Launch pilot with small user group
- Collect feedback and iterate
- Apply for regulatory approval
- Prepare for commercial launch

---

## 11. References

### 11.1 3GPP Specifications
- 3GPP TS 32.240 V18.9.0 - Charging Architecture and Principles
- 3GPP TS 32.290 V20.1.0 - Service Based Interface for Charging
- 3GPP TS 32.291 V20.1.0 - Nchf Converged Charging Service
- 3GPP TS 32.254 V18.4.0 - Exposure Function Northbound APIs Charging
- 3GPP TS 32.255 V18.0.0 - 5G Data Connectivity Charging
- 3GPP TS 23.501 V18.6.0 - 5G System Architecture
- 3GPP TS 23.222 V18.2.0 - Common API Framework (CAPIF)
- 3GPP TS 29.222 V20.1.0 - CAPIF Service APIs
- 3GPP TS 28.816 V18.0.0 - CP Data Transfer Charging with NEF

### 11.2 Regulatory Documents
- Kenya Information and Communications Act, 1998 (Cap. 411A)
- The Kenya Information and Communications (General Licensing) Regulations, 2025
- Telecommunications Market Structure Review - Communications Authority of Kenya
- Revised Telecommunications Market Structure February 2026

### 11.3 Industry Resources
- 3GPP Charging Enhancements Rel-19
- Nokia Network Exposure Function Documentation
- Oracle Cloud Native Core NEF User Guide
- free5GC CHF Design Document
- P1sec 5G Charging Security Analysis
- Analysys Mason 5G Charging Standards Perspective

### 11.4 Standards Organizations
- 3GPP (3rd Generation Partnership Project) - https://www.3gpp.org
- ETSI (European Telecommunications Standards Institute) - https://www.etsi.org
- Communications Authority of Kenya - https://www.ca.go.ke

---

**Document Classification:** Technical Research Report
**Prepared For:** DataVault Project
**Confidentiality:** Internal Use Only
