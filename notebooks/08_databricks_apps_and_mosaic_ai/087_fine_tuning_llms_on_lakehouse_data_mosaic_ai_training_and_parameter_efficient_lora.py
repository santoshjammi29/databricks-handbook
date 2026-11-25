# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 087. Fine-Tuning LLMs on Lakehouse Data: Mosaic AI Training & Parameter-Efficient LoRA
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Architect` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A healthcare enterprise wants to fine-tune an open-source LLM (Llama-3-8B) on proprietary clinical trial notes stored in Unity Catalog to improve medical term comprehension while keeping training data private.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure a Mosaic AI Model Training run using parameter-efficient fine-tuning (LoRA), preparing Delta Lake training datasets, tuning hyperparameters, and registering the fine-tuned adapter into Unity Catalog.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Mosaic AI Model Training provides managed, multi-node GPU training for foundation models. It supports Parameter-Efficient Fine-Tuning (PEFT/LoRA) and full fine-tuning directly on Delta Lake data, saving checkpoints to Unity Catalog Volumes.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Mosaic AI Training Configuration Specification
# MAGIC
# MAGIC Define training hyperparameters and data input paths for LoRA fine-tuning.
# COMMAND ----------

fine_tuning_spec = {
    "model_name": "meta-llama/Meta-Llama-3-8B-Instruct",
    "train_data_path": "/Volumes/prod_lakehouse/clinical_ai/training_data/train.jsonl",
    "eval_data_path": "/Volumes/prod_lakehouse/clinical_ai/training_data/eval.jsonl",
    "output_model_name": "prod_lakehouse.clinical_ai.llama3_medical_specialist",
    "training_method": "LORA",
    "hyperparameters": {
        "learning_rate": "5e-5",
        "num_epochs": 3,
        "lora_r": 16,
        "lora_alpha": 32,
        "batch_size": 4
    }
}

print(f"Base Model: {fine_tuning_spec['model_name']}")
print(f"Training Technique: {fine_tuning_spec['training_method']} (r={fine_tuning_spec['hyperparameters']['lora_r']})")
print(f"Output Registry Target: {fine_tuning_spec['output_model_name']}")
assert fine_tuning_spec["training_method"] == "LORA"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Parameter-Efficient Tuning**: LoRA trains small adapter weights, reducing GPU training costs by up to 90%.
# MAGIC - **Data Privacy**: Training data never leaves the customer's cloud storage or Databricks environment.
# MAGIC - **Automated Registry**: Finished models are registered directly into Unity Catalog for 1-click serving.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What are the benefits of LoRA (Low-Rank Adaptation) for fine-tuning LLMs on enterprise data?
# MAGIC 2. How does Mosaic AI Training stream datasets from Delta Lake during distributed GPU training?
