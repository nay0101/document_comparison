from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import base64
import pymupdf
from helpers.document_processor import DocumentProcessor

load_dotenv()

pdf_file = "./data_sources/pd_product transparency and disclosure_dec2024.pdf"
document_processor = DocumentProcessor()
with open(pdf_file, "rb") as file:
    images = document_processor.pdf_to_image(file.read(), [45, 46, 47])

home_loan_content = """

1
 
MG PDS ver1 Feb 2025 1 
PRODUCT DISCLOSURE SHEET  
(Versi Bahasa Malaysia)   
 Kindly  read  and  understand  this  Product  Disclosure  Sheet 
together  with  the  terms  in  the  Letter  of  Offer  before  you 
decide to take up the product below: 
 
 Please tick whichever is applicable in this document. 
 
Please  do  not  hesitate  to  contact  Hong  Leong  Bank  (“the 
Bank”) for clarification, if required. 
 
 
<Product Name> 
Date: <<Date Letter of Offer issued>> 
1. What is this product about?  
 
 
  Hong Leong Housing Loan/ 
      Shop Loan  
 
This  facility  is  calculated  on  a  variable  rate  basis  and  you  are  offering 
your property as a security to the Bank.  
 
It offers flexibility in repayment and interest savings.   
 
Any  excess  payment  received  after deducting your  instalment  and  any 
charges payable, is deemed as an “Advance Payment”.  
 
Advance Payment will not be considered as prepayment and thereafter 
will affect your loan outstanding balance for interest calculation 
purposes.      Interest  is  calculated  on  the  Eligible  Outstanding  Balance, 
which is the difference between the loan outstanding balance (inclusive 
of charges) (“Outstanding Balance”) and the Advance Payment or up 
to 30% of the Outstanding Balance, whichever is lower. 
 
Withdrawals are allowed from excess payment under Advance Payment 
with written notice.  
 
 
  Hong Leong MortgagePlus 
      Housing Loan/Shop Loan  
       
 
This  facility  is  calculated  on  a  variable  rate  basis  and  you  are  offering 
your property as a security to the Bank.  
 
It offers flexibility in repayment and interest savings by linking your loan 
account directly to your MortgagePlus Current Account.  
 
Any  excess  payment  received  after deducting your  instalment  and  any 
charges  payable,  is  deemed  as  “Advance  Payment”;  which  is  not 
considered prepayment and will affect your loan outstanding balance for 
interest calculation purposes. Interest is calculated  on the Eligible 
Outstanding Balance which is the difference between the loan 
outstanding  balance  (inclusive  of  charges)  (“Outstanding  Balance”) 
and  the  sum  of  the  Advance  Payment  and  the  credit  balance  in  your 
MortgagePlus Current Account or up to 70% of the Outstanding 
Balance, whichever is lower.  
 
You can repay this facility and withdraw excess payment on top of your 
instalment payable from your MortgagePlus Current Account at 
anytime. 
 
 
 
 
MG PDS ver1 Feb 2025 2 
 
 Hong Leong Special Housing 
Loan/ Housing Guarantee 
Scheme 
 
This  facility  is  calculated  on  a  variable  rate  basis  and  you  are  offering 
your property as a security to the Bank. 
 
This facility is granted to you subject to you fulfilling all the criteria under 
Bank Negara Malaysia’s guideline on “Lending/Financing to the Priority 
Sectors” or Syarikat Jaminan Kredit Perumahan (SJKP). 
 
 
  HLB Solar Plus Loan 
 
This  facility  is  granted  to  you  for  the  purpose  of  installation  of  solar 
panels. 
 
This  facility  is  calculated  on  a  variable  rate  basis  and  you  are  offering 
your property as a security to the Bank. 
 
It offers flexibility in repayment and interest savings.   
 
Any  excess  payment  received  after deducting your  instalment  and  any 
charges payable, is deemed as an “Advance Payment”. 
 
Advance Payment will not be considered as prepayment and thereafter 
will affect your loan outstanding balance for interest calculation 
purposes.  Interest  is  calculated  on  the  Eligible  Outstanding  Balance, 
which is the difference between the loan outstanding balance (inclusive 
of charges) (“Outstanding Balance”) and the Advance Payment or up 
to 30% of the Outstanding Balance, whichever is lower. 
 
Withdrawals are allowed from excess payment under Advance Payment 
with written notice. 
     
 
  HLB Mortgage Overdraft 
 
This  facility  is  granted  to  you for  the  purpose  of  purchasing  properties, 
refinancing a loan or investment opportunity. 
 
This  facility  is  calculated  on  a  variable  rate  basis  and  you  are  offering 
your property as a security to the Bank. 
 
It  offers  flexibility  in  repayment  &  withdrawal  of  funds  within  the  facility 
limits through Overdraft Current Account. 
 
The  facility  is  subjected  to  monthly  reduction  &  the  facility  limit  will  be 
reset to zero by the time you reach 65 years old in which for: 
(a)  Combination of Term Loan & Overdraft – monthly reduction 
commencing from the 61st month from the date of full availability of 
Overdraft Facility. 
(b)  Overdraft  only  –  monthly  reduction  commencing  from  the  37th 
month from the date of full availability of Overdraft Facility. 
 
For  combination  of  Overdraft  Facility  with  Term  Loan,  the  Overdraft 
Facility will only be available once the Term Loan is fully disbursed. 
  
 
2. What do I get from this product? 
 
Facility 1 - <Product Name> 
Item Description 
Facility Amount RM <Total Amount Borrowed> 
Margin of Financing * <__>% 
Repayment Period <Approved Tenure> months 

"""
user_message = [
    {
        "type": "text",
        "text": f"{home_loan_content} - does this follow the template order?",
    },
]
for image in images:
    user_message.append(
        {
            "type": "image_url",
            "image_url": {"url": image},
        },
    )
model = ChatOpenAI(model="gpt-4o")
message = HumanMessage(content=user_message)
response = model.invoke([message])
print(response.content)
