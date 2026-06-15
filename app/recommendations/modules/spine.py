"""Spine Surgery Decision Support — Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/spineLogic.ts (assessSpine).

Based on:
- NASS Evidence-Based Clinical Guidelines 2024 (PMID: 38272161)
- ACS/AANS/CNS Choosing Wisely Recommendations 2023
- North American Spine Society (NASS) Low Back Pain Guidelines 2024
- Lancet Low Back Pain Series 2018 (PMID: 29573870)
- SPORT Trial (Spine Patient Outcomes Research Trial) (PMID: 16914701)
- ACDF vs Arthroplasty: Cochrane 2024 (PMID: 38451851)
"""

from __future__ import annotations

from app.recommendations.jslib import num

LOGIC_KEY = "spine"


def detect_red_flags(data: dict) -> list[str]:
    flags: list[str] = []
    if data.get("cauda_equina_syndrome"):
        flags.append("Cauda equina syndrome — EMERGENT surgical decompression required")
    if data.get("progressiveNeurologicDeficit"):
        flags.append("Progressive neurologic deficit — urgent surgical evaluation")
    if data.get("malignancy"):
        flags.append("Known or suspected malignancy — urgent oncologic evaluation")
    if data.get("infection"):
        flags.append(
            "Spinal infection (discitis/osteomyelitis/epidural abscess) — urgent infectious disease + spine surgery evaluation"
        )
    if data.get("fracture") and data.get("spinalInstability"):
        flags.append("Unstable spinal fracture — urgent surgical stabilization")
    if data.get("neurologicStatus") == "cauda_equina":
        flags.append("Cauda equina syndrome on exam — emergent decompression")
    if data.get("neurologicStatus") == "myelopathy_severe":
        flags.append("Severe myelopathy — urgent surgical decompression")
    return flags


def detect_choosing_wisely_flags(data: dict) -> list[str]:
    flags: list[str] = []
    pain_duration_weeks = num(data.get("painDurationWeeks"), 0)
    # Don't image low back pain without red flags in first 6 weeks
    if (
        data.get("imagingFindings") != "no_imaging"
        and pain_duration_weeks < 6
        and len(detect_red_flags(data)) == 0
    ):
        flags.append(
            "Imaging obtained <6 weeks without red flags: not recommended per NASS/ACR Appropriateness Criteria — imaging rarely changes management in acute LBP"
        )
    # Don't operate on imaging findings without clinical correlation
    if (not data.get("imagingClinicalCorrelation")) and data.get("patientPrefersSurgery"):
        flags.append(
            "Imaging findings without clinical correlation: surgery not indicated — up to 80% of asymptomatic adults have disc bulges on MRI (Boden et al.)"
        )
    # Don't fuse for degenerative disc disease without radiculopathy
    if data.get("condition") == "lumbar_degenerative_disc" and data.get("neurologicStatus") == "intact":
        flags.append(
            "Lumbar fusion for degenerative disc disease without radiculopathy: not recommended — no evidence of superiority over intensive rehabilitation (Cochrane 2021)"
        )
    # Don't operate without adequate conservative trial (except red flags)
    if (
        data.get("conservativeTrialDuration") == "none"
        or data.get("conservativeTrialDuration") == "less_than_6_weeks"
    ):
        if len(detect_red_flags(data)) == 0:
            flags.append(
                "Surgery without adequate conservative trial (≥6-12 weeks): not recommended for non-emergent conditions — most patients improve with conservative care"
            )
    # Psychosocial factors — poor surgical outcomes
    if data.get("psychosocialFactors"):
        flags.append(
            "Psychosocial yellow flags: depression, anxiety, catastrophizing, or work-related factors predict poor surgical outcomes — address before surgery"
        )
    return flags


def assess(data: dict) -> dict:
    red_flags = detect_red_flags(data)
    choosing_wisely_flags = detect_choosing_wisely_flags(data)
    warnings: list[str] = []
    next_steps: list[str] = []

    # ── EMERGENT: Cauda equina syndrome ──
    if data.get("cauda_equina_syndrome") or data.get("neurologicStatus") == "cauda_equina":
        return {
            "decision": "surgery_urgent",
            "decisionLabel": "EMERGENT Surgical Decompression",
            "urgency": "emergent",
            "surgicalProcedure": "Emergency lumbar decompression (laminectomy/discectomy) within 24-48 hours",
            "surgicalRationale": "Cauda equina syndrome: surgical decompression within 24-48 hours associated with significantly better neurologic recovery. Delay increases risk of permanent bowel/bladder dysfunction.",
            "redFlagsPresent": red_flags,
            "choosingWiselyFlags": [],
            "naturalHistoryPrognosis": "Without surgery: high risk of permanent bowel/bladder dysfunction and lower extremity weakness",
            "surgicalBenefit": "Surgery within 24-48 hours: significantly improved neurologic recovery vs delayed surgery",
            "keyWarnings": ["EMERGENT: Do not delay — cauda equina syndrome is a surgical emergency"],
            "nextSteps": [
                "STAT MRI lumbar spine (if not already obtained)",
                "Emergent spine surgery consultation",
                "NPO, IV access, foley catheter",
                "OR within 24-48 hours (sooner if complete CES)",
            ],
            "rationale": "Cauda equina syndrome is a surgical emergency. Decompression within 24-48 hours is strongly recommended to maximize neurologic recovery.",
            "evidenceLevel": "Strong",
            "guidelineSource": "NASS 2024; ACS/AANS Emergency Guidelines",
        }

    # ── URGENT: Progressive neurologic deficit or severe myelopathy ──
    if data.get("progressiveNeurologicDeficit") or data.get("neurologicStatus") == "myelopathy_severe":
        procedure = (
            "Cervical decompression (ACDF or posterior laminectomy/fusion) — within 1-2 weeks"
            if data.get("condition") == "cervical_myelopathy"
            else "Lumbar decompression — within 1-2 weeks"
        )
        return {
            "decision": "surgery_urgent",
            "decisionLabel": "Urgent Surgical Decompression (within 1-2 weeks)",
            "urgency": "urgent",
            "surgicalProcedure": procedure,
            "surgicalRationale": "Progressive neurologic deficit or severe myelopathy: urgent decompression to prevent permanent neurologic injury.",
            "redFlagsPresent": red_flags,
            "choosingWiselyFlags": choosing_wisely_flags,
            "naturalHistoryPrognosis": "Progressive neurologic deficit: high risk of permanent deficit without timely decompression",
            "surgicalBenefit": "Decompression prevents further neurologic deterioration; recovery depends on duration and severity of deficit",
            "keyWarnings": ["Urgent: schedule surgery within 1-2 weeks — do not delay for extended conservative trial"],
            "nextSteps": [
                "MRI spine (if not obtained within past 4-6 weeks)",
                "Urgent spine surgery consultation",
                "Neurologic examination documentation",
                "Surgical planning: ACDF vs posterior approach for cervical myelopathy",
            ],
            "rationale": "Progressive neurologic deficit or severe myelopathy requires urgent surgical decompression. Natural history is unfavorable without surgery.",
            "evidenceLevel": "Strong",
            "guidelineSource": "NASS 2024; AANS/CNS Cervical Myelopathy Guidelines",
        }

    # ── Cervical myelopathy (mild-moderate) ──
    if data.get("condition") == "cervical_myelopathy" and (
        data.get("neurologicStatus") == "myelopathy_mild"
        or data.get("neurologicStatus") == "myelopathy_moderate"
    ):
        return {
            "decision": "surgery_recommended",
            "decisionLabel": "Surgery Recommended (Cervical Decompression)",
            "urgency": "elective",
            "surgicalProcedure": "ACDF (1-2 levels) or posterior laminoplasty/laminectomy-fusion (multilevel)",
            "surgicalRationale": "Mild-moderate cervical myelopathy: surgery prevents progression and improves functional outcomes. Natural history is unpredictable — stepwise deterioration common.",
            "redFlagsPresent": red_flags,
            "choosingWiselyFlags": choosing_wisely_flags,
            "naturalHistoryPrognosis": "Mild myelopathy: 20-60% deteriorate over 3-5 years without surgery. Moderate myelopathy: higher risk of deterioration.",
            "surgicalBenefit": "Surgery stabilizes or improves myelopathy in 80-90% of patients. Earlier surgery = better outcomes.",
            "keyWarnings": [
                w
                for w in [
                    "Psychosocial factors present: address before surgery — impacts recovery"
                    if data.get("psychosocialFactors")
                    else "",
                    "Smoking cessation: reduces pseudarthrosis risk after ACDF by 50%"
                    if data.get("smoker")
                    else "",
                ]
                if w
            ],
            "nextSteps": [
                "MRI cervical spine with STIR sequences",
                "Spine surgery consultation",
                "Discuss ACDF vs arthroplasty (for 1-2 level disease): arthroplasty preserves motion, reduces adjacent segment disease",
                "Smoking cessation if applicable",
                "Pre-operative optimization: glucose control if diabetic",
            ],
            "rationale": "Cervical myelopathy: surgery is recommended for mild-moderate disease to prevent progression. ACDF and arthroplasty have equivalent outcomes for 1-2 levels (Cochrane 2024).",
            "evidenceLevel": "Strong",
            "guidelineSource": "NASS 2024 (PMID: 38272161); AANS/CNS Cervical Myelopathy Guidelines",
        }

    # ── Lumbar disc herniation with radiculopathy ──
    if data.get("condition") == "lumbar_disc_herniation" and data.get("neurologicStatus") == "radiculopathy_only":
        adequate_trial = (
            data.get("conservativeTrialDuration") == "6_to_12_weeks"
            or data.get("conservativeTrialDuration") == "more_than_12_weeks"
        )
        if not adequate_trial:
            next_steps.append("Continue conservative treatment: NSAIDs, physical therapy, activity modification")
            next_steps.append("Epidural steroid injection if pain not controlled with oral medications")
            next_steps.append("Reassess at 6-12 weeks: if no improvement, consider surgical consultation")
            return {
                "decision": "continue_conservative",
                "decisionLabel": "Continue Conservative Treatment (6-12 weeks)",
                "urgency": "not_indicated",
                "conservativeRecommendations": [
                    "NSAIDs (naproxen 500 mg BID or ibuprofen 600 mg TID) — first-line",
                    "Physical therapy: McKenzie method or directional preference exercises",
                    "Epidural steroid injection if inadequate pain control",
                    "Activity modification: avoid prolonged sitting/bending",
                    "Avoid opioids for non-surgical back pain (Choosing Wisely)",
                ],
                "redFlagsPresent": red_flags,
                "choosingWiselyFlags": choosing_wisely_flags,
                "naturalHistoryPrognosis": "Lumbar disc herniation: 80-90% resolve with conservative treatment within 6-12 weeks (SPORT trial)",
                "surgicalBenefit": "Surgery provides faster pain relief but equivalent outcomes at 1-2 years vs conservative care (SPORT trial)",
                "keyWarnings": [
                    w
                    for w in [
                        "Most disc herniations resolve spontaneously — surgery not indicated without adequate conservative trial",
                        "Psychosocial factors: poor predictor of surgical outcome — address before considering surgery"
                        if data.get("psychosocialFactors")
                        else "",
                    ]
                    if w
                ],
                "nextSteps": next_steps,
                "rationale": "Lumbar disc herniation with radiculopathy: 80-90% improve with conservative treatment within 6-12 weeks. Surgery is elective and provides faster relief but equivalent long-term outcomes (SPORT trial). Conservative trial required before surgery.",
                "evidenceLevel": "Strong",
                "guidelineSource": "NASS 2024 (PMID: 38272161); SPORT Trial (PMID: 16914701)",
            }
        # Adequate conservative trial failed
        return {
            "decision": "surgery_optional",
            "decisionLabel": "Surgery Optional (Microdiscectomy) — After Failed Conservative Trial",
            "urgency": "elective",
            "surgicalProcedure": "Lumbar microdiscectomy (minimally invasive preferred)",
            "surgicalRationale": "SPORT trial: surgery provides faster pain relief and functional improvement vs continued conservative care after 6-12 weeks of failed conservative treatment.",
            "redFlagsPresent": red_flags,
            "choosingWiselyFlags": choosing_wisely_flags,
            "naturalHistoryPrognosis": "After 6-12 weeks of conservative treatment: 70-80% still improve without surgery over 1-2 years",
            "surgicalBenefit": "Microdiscectomy: faster pain relief (NRS improvement 3-4 points at 3 months), equivalent outcomes at 2 years vs conservative care",
            "keyWarnings": [
                w
                for w in [
                    "Psychosocial factors: poor predictor of surgical outcome — address before surgery"
                    if data.get("psychosocialFactors")
                    else "",
                    "Smoking: increases risk of recurrence and poor healing" if data.get("smoker") else "",
                    "Obesity (BMI ≥35): higher surgical complication risk — weight loss before elective surgery recommended"
                    if data.get("obesity")
                    else "",
                ]
                if w
            ],
            "nextSteps": [
                "MRI lumbar spine (if not obtained within past 3 months)",
                "Spine surgery consultation",
                "Shared decision-making: surgery vs continued conservative care — equivalent long-term outcomes",
                "Pre-operative optimization: smoking cessation, glucose control",
            ],
            "rationale": "After failed 6-12 week conservative trial: microdiscectomy is an option for faster pain relief. SPORT trial: equivalent outcomes at 2 years but faster improvement with surgery.",
            "evidenceLevel": "Strong",
            "guidelineSource": "NASS 2024 (PMID: 38272161); SPORT Trial (PMID: 16914701)",
        }

    # ── Lumbar stenosis ──
    if data.get("condition") == "lumbar_stenosis":
        adequate_trial = (
            data.get("conservativeTrialDuration") == "6_to_12_weeks"
            or data.get("conservativeTrialDuration") == "more_than_12_weeks"
        )
        if (not adequate_trial) and len(detect_red_flags(data)) == 0:
            return {
                "decision": "continue_conservative",
                "decisionLabel": "Continue Conservative Treatment",
                "urgency": "not_indicated",
                "conservativeRecommendations": [
                    "Physical therapy: flexion-based exercises (lumbar stenosis improves with flexion)",
                    "NSAIDs for pain management",
                    "Epidural steroid injections for neurogenic claudication",
                    "Walking program: gradual increase in distance",
                    "Aquatic therapy if land-based limited by pain",
                ],
                "redFlagsPresent": red_flags,
                "choosingWiselyFlags": choosing_wisely_flags,
                "naturalHistoryPrognosis": "Lumbar stenosis: 30-50% improve with conservative treatment; condition is slowly progressive in most patients",
                "surgicalBenefit": "Decompression: superior outcomes to conservative care for neurogenic claudication at 2-4 years (SPORT, SPORT-Stenosis)",
                "keyWarnings": ["Conservative trial recommended before surgery for non-emergent stenosis"],
                "nextSteps": [
                    "Physical therapy referral (flexion-based protocol)",
                    "Epidural steroid injection if neurogenic claudication",
                    "Reassess at 6-12 weeks",
                ],
                "rationale": "Lumbar stenosis: conservative treatment recommended as first-line. Surgery indicated after failed conservative trial or with progressive neurologic deficit.",
                "evidenceLevel": "Strong",
                "guidelineSource": "NASS 2024 (PMID: 38272161); SPORT Trial",
            }
        return {
            "decision": "surgery_recommended",
            "decisionLabel": "Surgical Decompression Recommended (After Failed Conservative Trial)",
            "urgency": "elective",
            "surgicalProcedure": "Lumbar decompression (laminectomy) ± fusion (if spondylolisthesis present)",
            "surgicalRationale": "SPORT-Stenosis: surgery superior to conservative care for neurogenic claudication at 2-4 years. Fusion added only if instability/spondylolisthesis present.",
            "redFlagsPresent": red_flags,
            "choosingWiselyFlags": choosing_wisely_flags,
            "naturalHistoryPrognosis": "Lumbar stenosis with failed conservative treatment: progressive functional decline likely without surgery",
            "surgicalBenefit": "Decompression: significant improvement in walking distance, pain, and function at 2-4 years (SPORT-Stenosis)",
            "keyWarnings": [
                w
                for w in [
                    "Fusion not routinely added to decompression — increases complication risk without benefit unless instability present",
                    "Osteoporosis: increases hardware failure risk — optimize bone density before surgery"
                    if data.get("osteoporosis")
                    else "",
                ]
                if w
            ],
            "nextSteps": [
                "MRI lumbar spine (if not obtained within past 6 months)",
                "Spine surgery consultation",
                "DEXA scan if osteoporosis suspected",
                "Cardiac evaluation if age >65 or significant comorbidities",
            ],
            "rationale": "Lumbar stenosis with failed conservative trial: decompression is recommended. SPORT-Stenosis: surgery superior to conservative care for neurogenic claudication at 2-4 years.",
            "evidenceLevel": "Strong",
            "guidelineSource": "NASS 2024 (PMID: 38272161); SPORT Trial (PMID: 16914701)",
        }

    # ── Degenerative disc disease without radiculopathy ──
    if data.get("condition") == "lumbar_degenerative_disc" and data.get("neurologicStatus") == "intact":
        return {
            "decision": "surgery_not_recommended",
            "decisionLabel": "Surgery NOT Recommended — Lumbar Fusion for Axial LBP",
            "urgency": "not_indicated",
            "conservativeRecommendations": [
                "Intensive multidisciplinary rehabilitation program (most effective for chronic LBP)",
                "Cognitive behavioral therapy (CBT) — Class I evidence for chronic LBP",
                "NSAIDs (short-term) — avoid long-term opioids",
                "Exercise therapy: aerobic + strengthening",
                "Mindfulness-based stress reduction (MBSR)",
                "Avoid bed rest — stay active",
            ],
            "redFlagsPresent": red_flags,
            "choosingWiselyFlags": choosing_wisely_flags,
            "naturalHistoryPrognosis": "Axial LBP from DDD: most patients improve with conservative treatment; surgery rarely provides durable benefit",
            "surgicalBenefit": "Lumbar fusion for axial LBP: no evidence of superiority over intensive rehabilitation (Cochrane 2021, Brox et al.)",
            "keyWarnings": [
                w
                for w in [
                    "Lumbar fusion for axial LBP without radiculopathy: NOT recommended per NASS 2024 and Choosing Wisely",
                    "Disc replacement for DDD: insufficient evidence to recommend over fusion or conservative care",
                    "Psychosocial factors: strongest predictor of chronic LBP — CBT and multidisciplinary rehabilitation are most effective"
                    if data.get("psychosocialFactors")
                    else "",
                ]
                if w
            ],
            "nextSteps": [
                "Intensive multidisciplinary rehabilitation program referral",
                "CBT referral for chronic pain",
                "Optimize medical management: NSAIDs, duloxetine (FDA-approved for chronic LBP)",
                "Avoid opioids for chronic non-specific LBP (Choosing Wisely)",
                "Reassess at 3-6 months",
            ],
            "rationale": "Lumbar fusion for axial LBP without neurologic deficit: NOT recommended. Cochrane 2021 and multiple RCTs show no superiority over intensive rehabilitation. Choosing Wisely: 'Don't perform lumbar spinal fusion for low back pain without neurologic deficit.'",
            "evidenceLevel": "Strong",
            "guidelineSource": "NASS 2024 (PMID: 38272161); Cochrane 2021; Lancet LBP Series (PMID: 29573870)",
        }

    # Default: continue conservative / multidisciplinary
    return {
        "decision": "continue_conservative",
        "decisionLabel": "Conservative Management Recommended",
        "urgency": "not_indicated",
        "conservativeRecommendations": [
            "Physical therapy",
            "NSAIDs for pain management",
            "Activity modification",
            "Reassess at 6-12 weeks",
        ],
        "redFlagsPresent": red_flags,
        "choosingWiselyFlags": choosing_wisely_flags,
        "naturalHistoryPrognosis": "Most spinal conditions improve with conservative treatment",
        "surgicalBenefit": "Surgery benefit depends on specific condition and adequate conservative trial",
        "keyWarnings": warnings,
        "nextSteps": [
            "Physical therapy referral",
            "Pain management optimization",
            "Reassess at 6-12 weeks",
            "Consider spine surgery consultation if no improvement",
        ],
        "rationale": "Conservative management is first-line for most spinal conditions without red flags.",
        "evidenceLevel": "Strong",
        "guidelineSource": "NASS 2024 (PMID: 38272161)",
    }
