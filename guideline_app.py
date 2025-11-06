import streamlit as st
from streamlit import session_state as ss
from helpers.guideline_comparison import GuidelineComparisonChain
from helpers.models import FinalComparisonResult
from helpers.reports import MarkdownPDFConverter
from helpers.document_processor import DocumentProcessor
from time import perf_counter
from uuid import uuid4
import os
from dotenv import load_dotenv
import json
from documentParseJson.md_extractor import extract_layout
import shutil
from pathlib import Path
import pandas as pd
import time

load_dotenv()

environment = os.getenv("ENVIRONMENT")
ss.default_chat_model = "gpt-5"
chat_model_list = [
    "gpt-5",
    # "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-flash-preview-05-20",
]
document_processor = DocumentProcessor()

if "result" not in ss:
    ss.result = None

if "chat_id" not in ss:
    ss.chat_id = uuid4()

if "chat_model" not in ss:
    ss.chat_model = ss.default_chat_model

if "formatted_guidelines" not in ss:
    ss.formatted_guidelines = None

if "formatted_document" not in ss:
    ss.formatted_document = None

if "clauses" not in ss:
    ss.clauses = None

if "titles" not in ss:
    ss.titles = []

if "compare_btn" in ss and ss.compare_btn:
    ss.chat_id = uuid4()

if ("guidelines" in ss and ss.guidelines is None) or ("doc" in ss and ss.doc is None):
    ss.result = None

if "guidelines" in ss and ss.guidelines is None:
    ss.formatted_guidelines = None
    ss.clauses = None
    ss.titles = []

if "doc" in ss and ss.doc is None:
    ss.formatted_document = None

if "sections" not in ss:
    ss.sections = None

if "time_taken" not in ss:
    ss.time_taken = None

if "guideline_info" not in ss:
    ss.guideline_info = []

ss.out_dir = Path("./guideline_app").resolve()
ss.compared_doc_dir = Path("./compared_doc").resolve()
# ss.result = [
#     {
#         "section": "16 Product Disclosure Sheet (PDS)",
#         "comparisons": [
#             {
#                 "clauseId": "S 16.1",
#                 "clause": 'S 16.1 A FSP shall provide a PDS (following the order and sequence of items as specified in the PDS templates provided in the Schedules) for financial consumers to make product comparisons and informed decisions. The FSP shall comply with the "Notes on PDS requirements" provided in the PDS templates.',
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "non-complied",
#                         "reason": "The provided PDS shows only a header, general instruction text, checkboxes, product name/date fields, and part of Section 1 “What is this product about?” for two loan variants. There is no evidence that the full order/sequence of items required by the relevant Schedule template is followed (e.g., key risks, fees/charges, eligibility, early settlement, default, important terms, contact points, complaint channels, etc.). No evidence of compliance with the “Notes on PDS requirements.”",
#                         "suggestions": [
#                             "Align the PDS strictly to the relevant Schedule template and its sequence for the specific product (e.g., housing loan).",
#                             "Add all required sections (e.g., product features, eligibility, risks, fees/charges, obligations, default consequences, cooling-off/lock-in, early settlement, contact/complaint info) in the exact order.",
#                             "Ensure all template notes (icons, wording, cross-references, comparison cues) are implemented and documented.",
#                         ],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "The provided document excerpt only shows a small section titled “13. Other housing/property loan packages available” listing product names. There is no visibility of the full PDS or confirmation that it follows the order/sequence or Notes in the Schedules.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "G 16.2",
#                 "clause": "G 16.2 For the avoidance of doubt, a FSP may use appropriate infographics, illustrations or colours to draw the attention of financial consumers to important terms in the PDS.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "This clause is permissive. The snapshot does not show any specific use of infographics/illustrations or colour cues to assess alignment; however, as it is guidance, strict compliance is not required.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "This is permissive guidance. The excerpt does not evidence use or non-use of infographics/illustrations/colours for important terms.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "G 16.3",
#                 "clause": "G 16.3 A FSP is encouraged to provide a PDS containing relevant product information that is tailored to the needs of financial consumers at the pre-contractual stage to facilitate consumers in making informed financial choices.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "non-complied",
#                         "reason": "Only introductory text and a partial product description are present. Key relevant information enabling informed choice (risks, fees, obligations, scenarios) is missing in the provided document portion; thus tailoring to consumer needs at pre-contractual stage is not evidenced.",
#                         "suggestions": [
#                             "Expand the PDS to include all relevant, consumer-centric information per template, with simple explanations and examples where helpful."
#                         ],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "Guidance item. The excerpt alone cannot establish whether the overall PDS is tailored at pre-contractual stage.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.4",
#                 "clause": "S 16.4 A FSP shall ensure the PDS does not exceed two A4 pages and ensure that the information is presented in an easily readable font size.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "non-complied",
#                         "reason": "The footer indicates “MG PDS ver1 Feb 2025 1” on page 1, but total page count is not shown. The content needed to meet Schedules would likely exceed what is shown; no explicit evidence that the entire PDS fits within two A4 pages. Font appears readable, but page-limit compliance cannot be confirmed.",
#                         "suggestions": [
#                             "Confirm and indicate that the complete PDS content fits within two A4 pages (e.g., “Page 1 of 2”).",
#                             "If content exceeds two pages, condense and redesign to meet the two-page limit without reducing font size below readable standards.",
#                         ],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "Only a single page snippet is shown without total page count of the PDS. Readability/font size across the entire PDS cannot be verified from this section alone.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.5",
#                 "clause": "S 16.5 A FSP shall use plain language and active verbs to make the PDS easy to read and understand.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "non-complied",
#                         "reason": "Several sentences use technical or formal terms without plain-language explanations, e.g., “calculated on a variable rate basis,” “Advance Payment will not be considered as prepayment,” “Eligible Outstanding Balance,” “inclusive of charges,” and long multi-clause sentences. These reduce readability and active/plain style.",
#                         "suggestions": [
#                             "Replace or explain technical terms in everyday language (e.g., “variable interest rate (rate can change over time)”).",
#                             "Use shorter, direct sentences and active verbs (“You can withdraw excess payments with written notice”).",
#                             "Add simple definitions beside terms like Advance Payment, Outstanding Balance, Eligible Outstanding Balance.",
#                         ],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "complied",
#                         "reason": "Within the provided section, wording is simple and direct (e.g., list of loan packages; “Should you require additional information… please log on to HLB’s website… or call…”). No complex or legalistic phrasing is present in this excerpt.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "G 16.6",
#                 "clause": "G 16.6 In relation to paragraph 16.5, keeping sentences short will make the PDS easier to read. Most plain language writing guides recommend an average sentence length of not more than twenty words per sentence.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "non-complied",
#                         "reason": "Multiple sentences exceed 20 words and contain several ideas, particularly in the facility descriptions and interest calculation explanations.",
#                         "suggestions": [
#                             "Edit text to target an average sentence length under 20 words; split complex explanations into bullets."
#                         ],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "complied",
#                         "reason": "Sentences in the excerpt are short and instructional. Bulleted lists are used. Average sentence length appears under twenty words in this section.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.7",
#                 "clause": "S 16.7 A FSP shall ensure the PDS is clearly distinguishable from other marketing materials to enable financial consumers to refer to the PDS for comparison and decision-making.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "non-complied",
#                         "reason": "The document is titled “PRODUCT DISCLOSURE SHEET” and carries the bank logo, but there is no explicit marker or layout element that makes it clearly distinct from marketing brochures. Without viewing surrounding materials or a statement such as “This is not a marketing material,” distinctness cannot be confirmed.",
#                         "suggestions": [
#                             "Add clear labeling and design cues such as a distinct PDS header banner, page footer with “Product Disclosure Sheet (PDS)”, and remove promotional wording.",
#                             "Ensure distribution processes separate the PDS from marketing leaflets (e.g., unique template code and disclaimer).",
#                         ],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "The excerpt alone does not show whether the document is a PDS distinct from marketing materials overall. No cover or distinguishing markers are provided for assessment.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.8",
#                 "clause": "S 16.8 A FSP shall put in place adequate measures to ensure financial consumers are guided to read and understand the PDS prior to entering into a contract. The extent to which the FSP implements these measures shall be commensurate with the complexity of the financial product (i.e. adopting a risk-based approach). The level of measures that must be put in place by FSPs for more complex products would be higher as compared to less complex products. For complex products, the FSP must take additional steps, such as calling customers post-sales, to confirm that the customers are aware of all key terms and risks of the product.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "This clause concerns internal measures and post-sales processes, which cannot be evidenced within the PDS document content provided.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "This requires evidence of operational measures beyond the text. The provided section offers no indication of guidance measures or post-sales calls.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "G 16.9",
#                 "clause": "G 16.9 In complying with paragraph 16.8, a FSP may require its front-line sales staff and intermediaries to advise financial consumers to read the PDS and explain the key information in the PDS, such as their obligations and product risks.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "Guidance on internal sales practices; not assessable from the provided PDS content.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "Guidance about internal practices. The excerpt provides no evidence regarding instructions to staff or intermediaries.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.10",
#                 "clause": "S 16.10 A FSP shall provide a copy of the PDS to financial consumers at the pre-contractual stage.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "Provision timing is a distribution practice not verifiable from the document alone.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "Operational requirement not verifiable from the excerpted text alone.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.11",
#                 "clause": "S 16.11 If it is not practical to provide the PDS at the pre-contractual stage, particularly for telemarketing transactions, a FSP shall direct financial consumers to its website to view, read or obtain a copy of the PDS.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "This addresses distribution via telemarketing and redirection to website; the PDS content does not evidence this practice.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "complied",
#                         "reason": "The section includes a direction where to obtain further information with a specific URL to the product page and a phone contact. This constitutes directing consumers to the website to view or obtain product information when not provided directly.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.12",
#                 "clause": "S 16.12 A FSP that distributes its financial products through intermediaries, including a digital channel, shall customise the information contained in the PDS according to the distribution channel. The FSP shall disclose specific charges to be borne by financial consumers for securing the sale through its intermediaries, such as the platform, processing or administrative fees, if any.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "Intermediary/digital-channel customization and disclosure of intermediary charges are not evidenced in the provided PDS. No mention of channel-specific fees.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "The excerpt neither confirms intermediary distribution nor discloses intermediary-specific fees. Without evidence of such channels in this section, applicability cannot be established.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.13",
#                 "clause": "S 16.13 For riders to an insurance/takaful product offering a variety of benefits, a FSP must provide a separate PDS for such riders. The FSP must provide the PDS for the riders together with the PDS for the basic insurance or takaful product.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "The product shown is a housing/mortgage loan, not an insurance/takaful product with riders.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "The product is housing/property loans, not insurance/takaful riders. Clause does not apply.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.14",
#                 "clause": "S 16.14 For financial products that are not set out in the Schedules, a FSP shall be guided by the format provided in the Schedules in producing a PDS on such products.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "Housing/mortgage loans are typically covered by Schedules. The extract does not state that this product is outside the Schedules; therefore assessment not applicable from the provided content.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "Housing/property loans are typically covered in Schedules; the excerpt does not show whether the product falls outside the Schedules.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.15",
#                 "clause": "S 16.15 A FSP offering an Islamic financial product must explain the applicable Shariah contract, including the key terms and conditions in the PDS.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "The product shown does not indicate that it is an Islamic product; no Shariah contract is referenced.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "The excerpt lists both conventional and possibly Islamic-branded accounts in payment channels but provides no Islamic product PDS content or Shariah contract details.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "G 16.16",
#                 "clause": "G 16.16 BNM reserves the right to require a FSP to make appropriate amendments to a PDS if information contained in the PDS is found to be inaccurate, incomplete or misleading.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "This is a regulatory reservation of rights; not assessable against the PDS content.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "This is a regulatory reservation; compliance cannot be assessed against the provided excerpt.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#             {
#                 "clauseId": "S 16.17",
#                 "clause": "S 16.17 A FSP shall immediately make appropriate amendments to the information contained in the PDS upon being informed by BNM in writing that the PDS is inaccurate or misleading.",
#                 "results": [
#                     {
#                         "snippet": '# PRODUCT DISCLOSURE SHEET\n\n(Versi Bahasa Malaysia)\n\nKindly read and understand this Product Disclosure Sheet together with the terms in the Letter of Offer before you decide to take up the product below:\n\n☑ Please tick whichever is applicable in this document.\n\nPlease do not hesitate to contact Hong Leong Bank ("the Bank") for clarification, if required.\n\n\\<Product Name\\>\n\nDate: \\<\\<Date Letter of Offer issued\\>\\>',
#                         "isComplied": "not-applicable",
#                         "reason": "This concerns post-notification actions by the FSP; not verifiable from the PDS document snapshot.",
#                         "suggestions": [],
#                     },
#                     {
#                         "snippet": "# 13. Other housing/property loan packages available\n\n- Hong Leong Housing Loan\n- Hong Leong MortgagePlus Housing Loan\n- Hong Leong Shop Loan\n- Hong Leong MortgagePlus Shop Loan\n- Hong Leong Special Housing Loan\n- Housing Guarantee Scheme\n- HLB Solar Plus Loan\n- HLB Mortgage Overdraft",
#                         "isComplied": "not-applicable",
#                         "reason": "Operational response requirement triggered by BNM notice; no evidence in the excerpt.",
#                         "suggestions": [],
#                     },
#                 ],
#             },
#         ],
#     }
# ]
# ss.result = [FinalComparisonResult(**item) for item in ss.result]
output_file = f"{ss.out_dir}/sections.json"

# with open(output_file, "r") as f:
#     ss.sections = json.loads(f.read())
#     ss.titles = [section["header"] for section in ss.sections]

st.header("Atenxion Guideline Compare Agent")
st.caption(f"Session ID: {ss.chat_id }")

# Custom CSS for pills
st.markdown(
    """
<style>
.attachment-pill {
    background-color: #e3f2fd;
    color: #1565c0;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 12px;
    margin: 2px 4px 2px 0;
    display: inline-block;
    border: 1px solid #bbdefb;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}

.attachment-pill:hover {
    background-color: #bbdefb;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

.attachment-pill-used {
    background-color: #e8f5e8;
    color: #2e7d32;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    margin: 2px 4px 2px 0;
    display: inline-block;
    border: 1px solid #c8e6c9;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
</style>
""",
    unsafe_allow_html=True,
)

st.divider()

st.file_uploader(
    label="Upload Central Bank Guideline Document", type=["pdf"], key="guidelines"
)

if ss.formatted_guidelines is None and ss.guidelines:
    # try:
    #     shutil.rmtree(ss.out_dir)
    # except FileNotFoundError:
    #     print("No existing directories to remove")
    ss.formatted_guidelines = True

    # Create progress placeholders
    progress_bar = st.progress(0.0)

    def update_progress(progress):
        progress_bar.progress(progress)

    # extract_layout(
    #     pdf=ss.guidelines.getvalue(),
    #     reasoning="minimal",
    #     verbosity="medium",
    #     model="gpt-5-mini",
    #     outdir=ss.out_dir,
    #     max_workers=8,
    #     mode="image",
    #     progress_callback=update_progress,
    # )

    # Clear progress indicators
    progress_bar.empty()

    with open(output_file, "r") as f:
        ss.sections = json.loads(f.read())
        ss.titles = [section["header"] for section in ss.sections]

st.multiselect(
    "Choose guideline section(s) to compare", key="section_title", options=ss.titles
)

if ss.sections:
    ss.clauses = [data for data in ss.sections if data["header"] in ss.section_title]

if ss.clauses:
    for index, data in enumerate(ss.clauses):
        ss[f"section_images_{index}"] = data["images"]
        st.title(body=f"{data['header']}")
        ss[f"title_{index}"] = data["header"]
        st.text_area(
            label="Guideline",
            value=data["content_md"],
            key=f"section_{index}",
            label_visibility="hidden",
            height=300,
        )
        st.multiselect(
            "Select Attachments (if any)",
            key=f"attachments_{index}",
            options=ss.titles,
        )
        ss[f"attachment_data_{index}"] = [
            item for item in ss.sections if item["header"] in ss[f"attachments_{index}"]
        ]

        if ss[f"attachment_data_{index}"]:
            for att_index, attachment in enumerate(ss[f"attachment_data_{index}"]):
                ss[f"attachment_images_{index}_{att_index}"] = attachment["images"]
                ss[f"attachment_{index}_{att_index}"] = attachment["content_md"]

st.file_uploader(label="Upload a Document to be Compared", type=["pdf"], key="doc")


# if ss.formatted_document is None and ss.doc:
#     try:
#         shutil.rmtree(ss.compared_doc_dir)
#     except FileNotFoundError:
#         print("No existing directories to remove")
#     ss.formatted_document = True

#     # Create progress placeholders for document processing
#     doc_progress_bar = st.progress(0.0)

#     def update_doc_progress(progress):
#         doc_progress_bar.progress(progress)

#     extract_layout(
#         pdf=ss.doc.getvalue(),
#         reasoning="minimal",
#         verbosity="medium",
#         model="gpt-5-mini",
#         outdir=ss.compared_doc_dir,
#         max_workers=8,
#         mode="image",
#         progress_callback=update_doc_progress,
#     )

#     # Clear progress indicators
#     time.sleep(2)
#     doc_progress_bar.empty()

compare_btn = st.button(
    label="Compare",
    type="secondary",
    key="compare_btn",
    disabled=ss.clauses is None or ss.doc is None,
)

if compare_btn:
    # Reset guideline_info for new comparison
    ss.guideline_info = []

    for i in range(len(ss.clauses)):
        images = ss[f"section_images_{i}"]
        clauses = ss[f"section_{i}"]
        title = ss[f"title_{i}"]
        attachments = []

        if ss[f"attachment_data_{i}"]:
            for j in range(len(ss[f"attachment_data_{i}"])):
                attachment_images = ss[f"attachment_images_{i}_{j}"]
                attachment_clauses = ss[f"attachment_{i}_{j}"]
                attachment_header = ss[f"attachment_data_{i}"][j]["header"]
                attachments.append(
                    {
                        "text": attachment_clauses,
                        "images": attachment_images,
                        "header": attachment_header,
                    }
                )

        ss.guideline_info.append(
            {
                "clauses": {"text": clauses, "images": images},
                "title": title,
                "attachments": attachments,
            }
        )

    chain = GuidelineComparisonChain(chat_model_name=ss.chat_model)
    start_time = perf_counter()

    with open(f"{ss.compared_doc_dir}/sections.json", "r") as f:
        doc = []
        json_sections = json.loads(f.read())
        # doc = "\n\n".join([section["content_md"] for section in json_sections])
        # doc_images = list(
        #     {img for section in json_sections for img in section.get("images", [])}
        # )
        # doc_dict = {"text": doc, "images": doc_images}
        for section in json_sections:
            doc.append(
                {
                    "text": section["content_md"],
                    "images": section.get("images", []),
                }
            )

    result = chain.invoke_chain(
        guidelines=ss.guideline_info,
        documents=doc,
        chat_id=f"guideline_{ss.chat_id}",
    )
    ss.result = result
    ss.time_taken = perf_counter() - start_time

if ss.result:
    final_result = ss.result
    with st.container():
        st.header(f"Comparison Details")
    # st.json(final_result, expanded=True)

    if len(final_result) > 0:
        report_generator = MarkdownPDFConverter()

        report = report_generator.generate_guideline_report(
            chat_model_name=ss.chat_model,
            chat_id=f"guideline_{ss.chat_id}",
            result=ss.result,
            time_taken=ss.time_taken,
            document_name=ss.doc.name if "doc" in ss and ss.doc is not None else None,
            guideline_info=ss.guideline_info,
        )
        st.download_button(
            "Download Report",
            data=report,
            file_name=f"report.pdf",
            mime="application/pdf",
        )
        st.divider()

        with st.container():
            for result in final_result:
                st.markdown(
                    f"<b style='font-size: 1.5rem;'>{result.section}</b>",
                    unsafe_allow_html=True,
                )

                # Display attachments used for this section as pills
                section_attachments = []
                for guideline in ss.guideline_info:
                    if guideline["title"] == result.section and guideline.get(
                        "attachments"
                    ):
                        section_attachments = guideline["attachments"]
                        break

                if section_attachments:
                    st.markdown("**Attachments Used:**")
                    # Create pills for attachments
                    attachment_pills = ""
                    for attachment in section_attachments:
                        attachment_header = attachment.get(
                            "header", "Unknown Attachment"
                        )
                        attachment_pills += f'<span class="attachment-pill">📎 {attachment_header}</span>'
                    st.markdown(attachment_pills, unsafe_allow_html=True)
                    st.markdown("")  # Add spacing

                for comparison in result.comparisons:
                    with st.container(border=True):
                        st.markdown(
                            f'<b style="font-size: 1.5rem;">{comparison.clause}</b>',
                            True,
                        )
                        st.divider()

                        for clause_result in comparison.results:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(
                                    "<b style='font-size: 1.2rem;'>Document Excerpt:</b>",
                                    True,
                                )
                                st.markdown(
                                    f"<p>{clause_result.snippet}</p>",
                                    True,
                                )

                            with col2:
                                st.markdown(
                                    "<b style='font-size: 1.2rem;'>Analysis:</b>", True
                                )
                                match clause_result.isComplied:
                                    case "complied":
                                        st.success("Complied", icon="✅")
                                    case "non-complied":
                                        st.error("Not Complied", icon="❌")
                                    case _:
                                        st.warning("Not Applicable", icon="⚠️")
                                st.markdown(
                                    f'<p style="font-size: 1rem;">{clause_result.reason}</p>',
                                    True,
                                )
                                if clause_result.suggestions:
                                    st.markdown("**Suggestions:**")
                                    for suggestion in clause_result.suggestions:
                                        st.markdown(f"- {suggestion}")
                            st.divider()


with st.sidebar:
    st.selectbox(
        label="Models",
        options=chat_model_list,
        index=chat_model_list.index(ss.default_chat_model),
        key="chat_model",
    )
