# Учебный план ML Engineer: middle+ → senior

Основа — 30 областей из диалога «Список навыков ML инженера».
Порядок следует зависимостям: инженерная база и математика → моделирование → production →
проектирование систем и ответственность → специализация LLM. Soft skills включены в соответствующие этапы.
Это рекомендуемый порядок; в боте можно выбрать любой раздел и проверить уже знакомую тему без объяснения.

Один раздел — отдельный урок: ориентировочно 15–25 минут вместе с вопросами и тестом.
Время на практику добавляется отдельно. При 3 приглашениях в день не обязательно проходить 3 новых урока:
приглашение может продолжить незаконченный урок, а сложный материал можно отложить.

Критерии готовности по этапам:

1. Инженерная база: собрать тестируемый Python-пакет, подготовить датасет SQL-запросом и объяснить статистическую оценку.
2. Моделирование: построить baseline и честную валидацию, обосновать метрики, сравнить модели и разобрать ошибки.
3. Production ML: выпустить контейнеризированный сервис с воспроизводимым обучением, мониторингом и откатом.
4. Уровень Senior: подготовить design doc с SLO, оценкой стоимости, отказами, альтернативами; провести ревью и разбор инцидента.
5. Специализация LLM: построить RAG-прототип, проверить retrieval и генерацию на наборе примеров, оценить стоимость и задержки.

Практические результаты выше выполняются самостоятельно; бот проверяет текстовое понимание и не исполняет код проектов.
Прохождение мини-тестов не заменяет практический опыт и не является профессиональной сертификацией.

Всего: 30 тем, 87 разделов.

## 1. Инженерная база

### 1. Python и Software Engineering

- **01.01 · Итераторы и управление ресурсами** — generators, iterators, context managers; чтение большого датасета.

- **01.02 · Типы и модель данных** — typing, dataclasses, decorators; контракты функций.

- **01.03 · Проектирование Python-кода** — ООП, композиция, SOLID, patterns, clean code; уместность абстракций.

- **01.04 · Из notebook в пакет** — архитектура проекта, dependency management, configuration, logging, exceptions.

- **01.05 · Тестирование ML-кода** — pytest, unit/integration/end-to-end, mocking; тесты данных и поведения.

- **01.06 · Git и CI/CD** — branches, commits, merge conflicts, code review, CI/CD.

- **01.07 · Конкурентность и производительность Python** — async, threads, multiprocessing, GIL, память, profiling.

### 2. Алгоритмы и структуры данных

- **02.01 · Сложность и коллекции** — Big O по времени и памяти; arrays, lists, hash maps, sets.

- **02.02 · Очереди и поиск** — stack, queue, heap, sorting, binary search; top-K.

- **02.03 · Графы и динамическое программирование** — trees, graphs, BFS, DFS, recursion, базовое DP.

### 3. Уточнение требований

- **03.01 · От запроса к критериям успеха** — пользователь, KPI, baseline, latency, объём данных, QPS, бюджет, цена ошибки.

### 4. SQL и обработка данных

- **04.01 · SQL для анализа** — JOIN, GROUP BY, подзапросы, CTE, NULL; дубликаты после соединений.

- **04.02 · Оконные функции** — window functions, ранжирование, лаги, временные агрегаты без утечек.

- **04.03 · Быстрые и корректные запросы** — indexes, query optimization, execution plans, transactions.

- **04.04 · Табличные вычисления** — NumPy, Pandas, Polars, vectorization, missing values, типы.

- **04.05 · Данные больше RAM** — Parquet, Arrow, serialization, chunking, основы Spark и distributed processing.

### 5. Математика для ML

- **05.01 · Линейная алгебра** — vectors, matrices, tensors, multiplication, dot product, norms, similarity.

- **05.02 · Спектральные методы** — eigenvalues/eigenvectors, SVD, PCA, embeddings; геометрическая интуиция.

- **05.03 · Вероятности** — random variables, distributions, expectation, variance, conditional probability, Bayes.

- **05.04 · Оценка параметров** — likelihood, MLE, MAP; связь с loss и регуляризацией.

- **05.05 · Статистические выводы** — sampling, confidence intervals, tests, p-value, significance, bootstrap.

- **05.06 · Эксперименты и причинность** — correlation vs causation, A/B testing, единица рандомизации, мощность.

- **05.07 · Градиенты и оптимизация** — derivatives, partial derivatives, gradients, chain rule, GD, SGD, Adam, learning rate, convexity.

## 2. Моделирование

### 6. Постановка ML-задачи

- **06.01 · Декомпозиция бизнес-проблемы** — business problem → ML formulation → data → metric → experiment → production → measurement; churn.

### 7. Основы ML и метрики

- **07.01 · Обобщение и регуляризация** — bias/variance, underfitting/overfitting, regularization, learning curves.

- **07.02 · Валидация без утечек** — train/validation/test, cross-validation, temporal/group split, data leakage.

- **07.03 · Признаки и подбор параметров** — feature engineering/selection, hyperparameter optimization, reproducibility.

- **07.04 · Метрики классификации** — precision, recall, F1, ROC-AUC, PR-AUC, log loss, class imbalance.

- **07.05 · Порог и калибровка** — calibration, threshold selection, цена ошибок, бизнес-метрики.

- **07.06 · Регрессия и ранжирование** — MAE, MSE, RMSE, R², MAPE; Precision@K, Recall@K, MAP, MRR, NDCG.

- **07.07 · Сдвиг данных** — distribution shift, concept drift; ограничения offline-оценки.

### 8. Классический ML

- **08.01 · Линейные модели** — Linear/Logistic Regression: assumptions, training, inference, complexity, failure modes.

- **08.02 · Деревья и случайный лес** — Decision Trees, Random Forest, bagging; strengths, weaknesses, complexity.

- **08.03 · Градиентный бустинг** — Gradient Boosting, XGBoost/LightGBM/CatBoost, категориальные признаки, early stopping.

- **08.04 · Методы расстояний и разделяющих поверхностей** — kNN, SVM, kernels, scaling, training/inference complexity.

- **08.05 · Обучение без учителя** — K-Means, DBSCAN, PCA, clustering, anomaly detection, оценка без меток.

### 9. Коммуникация

- **09.01 · Объяснять ML разным аудиториям** — объяснить drift инженеру ML, backend-инженеру и менеджеру; ограничения, неопределённость, следующий шаг.

### 10. Deep Learning и PyTorch

- **10.01 · Нейросети и backpropagation** — MLP, activation/loss functions, backpropagation, autograd.

- **10.02 · Стабильное обучение** — initialization, normalization, dropout, optimizers, learning-rate schedules.

- **10.03 · Архитектуры для изображений и последовательностей** — CNN, RNN, LSTM/GRU, attention, encoder/decoder.

- **10.04 · Training loop в PyTorch** — Dataset/DataLoader, custom modules/loss, train/eval, validation, checkpointing.

- **10.05 · GPU и распределённое обучение** — GPU training, mixed precision, distributed training basics, profiling, reproducibility.

## 3. Production ML

### 11. Linux и Docker

- **11.01 · Linux для диагностики** — filesystem, processes, signals, permissions, env, networking, bash, ssh, logs, CPU/RAM/disk.

- **11.02 · Контейнеризация** — Dockerfile, images/containers, volumes, networks, multi-stage builds, Docker Compose, optimization.

### 12. Базы данных и поиск

- **12.01 · PostgreSQL и транзакции** — indexes, ACID, isolation levels, transactions, query planning.

- **12.02 · NoSQL и кэш** — Redis, document databases, key-value stores; consistency и trade-offs.

- **12.03 · Векторный и полнотекстовый поиск** — FAISS, pgvector, Elasticsearch/OpenSearch, vector DB, exact vs approximate search.

### 13. Backend для ML

- **13.01 · API предсказаний** — HTTP, REST, API design, FastAPI, serialization, client → preprocessing → model → response.

- **13.02 · Нагрузка и обмен сообщениями** — async, queues, caching, WebSockets, gRPC, timeouts, retries, backpressure.

- **13.03 · Контракты и защита API** — authentication basics, validation, versioning, idempotency, error handling.

### 14. Техническая документация

- **14.01 · README, RFC и ADR** — README, design docs, RFC, Architecture Decision Records, API documentation, trade-offs.

- **14.02 · Отчёты и postmortem** — experiment reports, postmortems: факты, причины, меры, без поиска виноватых.

### 15. Data Engineering

- **15.01 · Надёжные data pipelines** — ETL/ELT, batch, warehouse/lake/lakehouse, schema evolution, data quality, idempotency.

- **15.02 · Streaming и оркестрация** — Kafka, Spark, Airflow, event time, late data, retries, backfills.

### 16. MLOps

- **16.01 · Воспроизводимые эксперименты** — experiment tracking, MLflow, model registry, dataset versioning, DVC, reproducibility.

- **16.02 · Пайплайн обучения** — pipelines, orchestration, Airflow/Dagster/Prefect, Kubeflow, feature stores, Feast, training-serving skew.

- **16.03 · Доставка модели** — model serving, batch/online inference, shadow/canary, A/B, rollback.

- **16.04 · Цикл переобучения** — data → training → validation → registry → deployment → monitoring → retraining, quality gates.

### 17. Cloud

- **17.01 · Облачные компоненты** — AWS/GCP/Azure на примере одного: compute, object storage, databases, containers, networking.

- **17.02 · Эксплуатация в облаке** — IAM, secrets, monitoring, autoscaling, зоны отказа, бюджет.

### 18. Kubernetes

- **18.01 · Базовые объекты** — Pod, Deployment, Service, ConfigMap, Secret, Ingress.

- **18.02 · Надёжный deployment** — requests/limits, autoscaling, health checks, rolling deployment, graceful shutdown.

### 19. Мониторинг ML

- **19.01 · Наблюдаемость сервиса** — latency, throughput, error rate, CPU/GPU utilization, alerting, SLO.

- **19.02 · Качество после релиза** — model metrics, delayed labels, feature distributions, data/concept/prediction drift, data quality.

## 4. Уровень Senior

### 20. Ownership

- **20.01 · Ответственность за результат** — от требований до production, взаимодействие с data/backend/product, мониторинг, rollback, инциденты.

### 21. System Design

- **21.01 · Основы распределённых систем** — latency, throughput, scalability, availability, consistency, caching, queues, batch/streaming, storage, failure handling, observability, cost.

- **21.02 · Рекомендательная система** — events → Kafka → feature pipeline/store → candidate generation → ranking → API; cold start.

- **21.03 · Поиск и рекламное ранжирование** — search/ranking, ad ranking, retrieval, online/offline metrics, experiments.

- **21.04 · Fraud, spam и аномалии** — fraud detection, spam detection, anomaly detection, class imbalance, delayed labels, adversarial drift.

- **21.05 · Churn от идеи до эксплуатации** — churn prediction, actionable intervention, batch scoring, causal effect, cost, end-to-end design.

### 22. Производительность

- **22.01 · Поиск узкого места** — CPU/GPU, RAM/VRAM, I/O, vectorization, batching, concurrency, multiprocessing, caching, profiling.

- **22.02 · Оптимизация inference** — latency/throughput, batch size, quantization, ONNX, TensorRT, model compression, quality regression.

### 23. Безопасность

- **23.01 · Данные и доступ** — authentication/authorization, secrets, IAM, encryption, PII, data/model access controls.

- **23.02 · Защита ML-сервиса** — dependency vulnerabilities, API security, supply chain, abuse, prompt injection для LLM.

### 24. Стоимость

- **24.01 · Экономика ML-системы** — training, GPU inference, storage, network, databases, LLM API, autoscaling; quality/latency/cost/complexity.

### 25. Принятие решений

- **25.01 · Аргументировать trade-offs** — LightGBM vs NN, batch vs real-time, pgvector vs vector DB, external API vs own serving; обратимость решений.

### 26. Приоритизация

- **26.01 · Выбирать работу с максимальной пользой** — must-have/nice-to-have, impact/effort, accuracy vs latency, риск, короткие эксперименты.

### 27. Работа с неопределённостью

- **27.01 · Расследовать размытую проблему** — рекомендации стали хуже: гипотезы, данные, проверка, ограничения, decision log, критерии остановки.

### 28. Code Review

- **28.01 · Ревью инженерных решений** — correctness, readability, maintainability, coupling, architecture, performance, reliability; конструктивная обратная связь.

### 29. Менторинг

- **29.01 · Развивать самостоятельность коллег** — объяснение решений, code review, декомпозиция, совместный debugging, engineering practices, обратная связь.

## 5. Специализация LLM

### 30. Transformers и LLM

- **30.01 · Как устроен Transformer** — tokenization, embeddings, positional encoding, self/multi-head attention, encoder/decoder, context windows.

- **30.02 · Обучение и адаптация LLM** — pretraining, instruction tuning, SFT, LoRA/PEFT; fine-tuning vs RAG.

- **30.03 · Serving LLM** — inference, quantization, KV cache, batching, context windows, latency, memory.

- **30.04 · LLM-приложения и агенты** — prompting, structured outputs, tool/function calling, agents, границы полномочий.

- **30.05 · RAG и поиск** — embeddings, semantic search, chunking, reranking, vector DB, hybrid search.

- **30.06 · Оценка и ограничения LLM** — LLM evaluation, hallucination mitigation, guardrails, prompt injection, regression datasets.

- **30.07 · Проектирование LLM/RAG-сервиса** — end-to-end architecture, качество/стоимость/задержки, нужен ли LLM или достаточно ML/поиска/правил.
