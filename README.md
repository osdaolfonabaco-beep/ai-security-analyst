# 🤖 AI-Augmented Security Analyst

**A serverless log analysis pipeline that leverages Infrastructure as Code and Generative AI to automatically detect, analyze, and classify security threats from web server logs.**

This project demonstrates a complete, end-to-end cloud-native solution for modern security operations (SecOps). It ingests raw log files, processes them in a serverless environment, and uses a Large Language Model (LLM) to provide expert-level analysis of suspicious activities, effectively acting as an automated Tier 1 security analyst.

---

## 🏛️ Architecture

The entire system is deployed on AWS and managed via Terraform. The architecture is designed to be event-driven, scalable, and cost-effective.



1.  **Data Ingestion:** A new log file (`.log`) is uploaded to a dedicated **Amazon S3** bucket.
2.  **Event Trigger:** The S3 `ObjectCreated` event automatically triggers an **AWS Lambda** function.
3.  **Core Processing:** The Python-based Lambda function downloads the log file, parses it to count requests per IP, and identifies IPs that exceed a predefined suspicious activity threshold.
4.  **AI Enrichment:** For each suspicious IP, the function compiles a sample of relevant log entries and sends them to **Amazon Bedrock**. It invokes the **Anthropic Claude 3 Haiku** model with a carefully engineered prompt, asking it to act as a cybersecurity expert.
5.  **Analysis & Reporting:** The LLM returns a structured JSON object containing its analysis, including the probable attack type, a confidence level, and a recommended course of action.
6.  **Observability:** The entire process, including the AI's final report, is logged to **Amazon CloudWatch** for monitoring and auditing.

---

## ✨ Key Features

* **Fully Automated Pipeline:** Zero manual intervention required from log ingestion to final analysis.
* **Infrastructure as Code (IaC):** The entire cloud infrastructure is defined and managed using **Terraform**, ensuring reproducibility and version control.
* **Serverless & Scalable:** Built with AWS Lambda, the system scales automatically to handle any volume of logs and you only pay for what you use.
* **AI-Powered Threat Analysis:** Moves beyond simple IP counting. It uses a powerful LLM to understand the *context* and *intent* behind log patterns.
* **Actionable Intelligence:** The output isn't just data; it's a clear, concise, and actionable report in a structured JSON format.

---

## 🛠️ Tech Stack

* **Cloud Provider:** AWS
* **Core Services:** S3, Lambda, IAM, CloudWatch
* **AI Service:** Amazon Bedrock (Anthropic Claude 3 Haiku model)
* **Infrastructure as Code:** Terraform
* **Core Language:** Python 3.9
* **Key Python Libraries:** Boto3 (AWS SDK)

---

## 🚀 How to Deploy

To deploy this project in your own AWS account, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/osdaolfonabaco-beep/ai-security-analyst.git](https://github.com/osdaolfonabaco-beep/ai-security-analyst.git)
    cd ai-security-analyst
    ```
2.  **Configure AWS Credentials:** Ensure your AWS CLI is configured with the necessary permissions (`AdministratorAccess` for simplicity).

3.  **Prepare the Lambda package:**
    ```bash
    cd lambda_function
    zip ../lambda_function.zip main.py
    cd ..
    ```
4.  **Deploy with Terraform:**
    * Navigate to the Terraform directory: `cd terraform`
    * **Important:** Open `main.tf` and change the `bucket` name in the `aws_s3_bucket` resource to a globally unique name.
    * Initialize and apply:
        ```bash
        terraform init
        terraform apply
        ```
    * Confirm the deployment by typing `yes`.

5.  **Test the pipeline:** Upload a `.log` file to the newly created S3 bucket. You can use the `test_final.log` file included in this repository as an example.

6.  **Check the results:** Navigate to the Amazon CloudWatch service in your AWS console, find the log group named `/aws/lambda/SecurityLogAnalyzerIA`, and inspect the latest log stream to see the AI-generated report.

---

## 📄 Example AI-Generated Report

After processing a log file containing a potential reconnaissance attack, the system produces the following structured output in CloudWatch:

```json
{
  "ip_address": "185.191.171.12",
  "probable_attack_type": "Scanning/Reconnaissance",
  "confidence_level": "High",
  "recommended_action": "Block IP at firewall"
}
