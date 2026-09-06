"""Stable lesson IDs: never reorder existing sections without a data migration.

Adapted from the user's 'Список навыков ML инженера' conversation.
Topics are grouped by prerequisites; professional skills appear throughout.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Lesson:
    id: str
    topic_id: int
    title: str
    scope: str


@dataclass(frozen=True)
class Topic:
    id: int
    stage: str
    title: str
    lessons: tuple[Lesson, ...]


# Each section is a 15–25 minute lesson, including open-ended assessment.
CATALOG = [
    (
        "1. Инженерная база",
        "Python и Software Engineering",
        [
            (
                "Итераторы и управление ресурсами",
                "generators, iterators, context managers; чтение большого датасета",
            ),
            ("Типы и модель данных", "typing, dataclasses, decorators; контракты функций"),
            (
                "Проектирование Python-кода",
                "ООП, композиция, SOLID, patterns, clean code; уместность абстракций",
            ),
            (
                "Из notebook в пакет",
                "архитектура проекта, dependency management, configuration, logging, exceptions",
            ),
            (
                "Тестирование ML-кода",
                "pytest, unit/integration/end-to-end, mocking; тесты данных и поведения",
            ),
            ("Git и CI/CD", "branches, commits, merge conflicts, code review, CI/CD"),
            (
                "Конкурентность и производительность Python",
                "async, threads, multiprocessing, GIL, память, profiling",
            ),
        ],
    ),
    (
        "1. Инженерная база",
        "Алгоритмы и структуры данных",
        [
            ("Сложность и коллекции", "Big O по времени и памяти; arrays, lists, hash maps, sets"),
            ("Очереди и поиск", "stack, queue, heap, sorting, binary search; top-K"),
            ("Графы и динамическое программирование", "trees, graphs, BFS, DFS, recursion, базовое DP"),
        ],
    ),
    (
        "1. Инженерная база",
        "Уточнение требований",
        [
            (
                "От запроса к критериям успеха",
                "пользователь, KPI, baseline, latency, объём данных, QPS, бюджет, цена ошибки",
            )
        ],
    ),
    (
        "1. Инженерная база",
        "SQL и обработка данных",
        [
            ("SQL для анализа", "JOIN, GROUP BY, подзапросы, CTE, NULL; дубликаты после соединений"),
            ("Оконные функции", "window functions, ранжирование, лаги, временные агрегаты без утечек"),
            ("Быстрые и корректные запросы", "indexes, query optimization, execution plans, transactions"),
            ("Табличные вычисления", "NumPy, Pandas, Polars, vectorization, missing values, типы"),
            (
                "Данные больше RAM",
                "Parquet, Arrow, serialization, chunking, основы Spark и distributed processing",
            ),
        ],
    ),
    (
        "1. Инженерная база",
        "Математика для ML",
        [
            (
                "Линейная алгебра",
                "vectors, matrices, tensors, multiplication, dot product, norms, similarity",
            ),
            (
                "Спектральные методы",
                "eigenvalues/eigenvectors, SVD, PCA, embeddings; геометрическая интуиция",
            ),
            (
                "Вероятности",
                "random variables, distributions, expectation, variance, conditional probability, Bayes",
            ),
            ("Оценка параметров", "likelihood, MLE, MAP; связь с loss и регуляризацией"),
            (
                "Статистические выводы",
                "sampling, confidence intervals, tests, p-value, significance, bootstrap",
            ),
            (
                "Эксперименты и причинность",
                "correlation vs causation, A/B testing, единица рандомизации, мощность",
            ),
            (
                "Градиенты и оптимизация",
                "derivatives, partial derivatives, gradients, chain rule, GD, SGD, Adam, learning rate, convexity",
            ),
        ],
    ),
    (
        "2. Моделирование",
        "Постановка ML-задачи",
        [
            (
                "Декомпозиция бизнес-проблемы",
                "business problem → ML formulation → data → metric → experiment → production → measurement; churn",
            )
        ],
    ),
    (
        "2. Моделирование",
        "Основы ML и метрики",
        [
            (
                "Обобщение и регуляризация",
                "bias/variance, underfitting/overfitting, regularization, learning curves",
            ),
            (
                "Валидация без утечек",
                "train/validation/test, cross-validation, temporal/group split, data leakage",
            ),
            (
                "Признаки и подбор параметров",
                "feature engineering/selection, hyperparameter optimization, reproducibility",
            ),
            ("Метрики классификации", "precision, recall, F1, ROC-AUC, PR-AUC, log loss, class imbalance"),
            ("Порог и калибровка", "calibration, threshold selection, цена ошибок, бизнес-метрики"),
            ("Регрессия и ранжирование", "MAE, MSE, RMSE, R², MAPE; Precision@K, Recall@K, MAP, MRR, NDCG"),
            ("Сдвиг данных", "distribution shift, concept drift; ограничения offline-оценки"),
        ],
    ),
    (
        "2. Моделирование",
        "Классический ML",
        [
            (
                "Линейные модели",
                "Linear/Logistic Regression: assumptions, training, inference, complexity, failure modes",
            ),
            (
                "Деревья и случайный лес",
                "Decision Trees, Random Forest, bagging; strengths, weaknesses, complexity",
            ),
            (
                "Градиентный бустинг",
                "Gradient Boosting, XGBoost/LightGBM/CatBoost, категориальные признаки, early stopping",
            ),
            (
                "Методы расстояний и разделяющих поверхностей",
                "kNN, SVM, kernels, scaling, training/inference complexity",
            ),
            ("Обучение без учителя", "K-Means, DBSCAN, PCA, clustering, anomaly detection, оценка без меток"),
        ],
    ),
    (
        "2. Моделирование",
        "Коммуникация",
        [
            (
                "Объяснять ML разным аудиториям",
                "объяснить drift инженеру ML, backend-инженеру и менеджеру; ограничения, неопределённость, следующий шаг",
            )
        ],
    ),
    (
        "2. Моделирование",
        "Deep Learning и PyTorch",
        [
            ("Нейросети и backpropagation", "MLP, activation/loss functions, backpropagation, autograd"),
            (
                "Стабильное обучение",
                "initialization, normalization, dropout, optimizers, learning-rate schedules",
            ),
            (
                "Архитектуры для изображений и последовательностей",
                "CNN, RNN, LSTM/GRU, attention, encoder/decoder",
            ),
            (
                "Training loop в PyTorch",
                "Dataset/DataLoader, custom modules/loss, train/eval, validation, checkpointing",
            ),
            (
                "GPU и распределённое обучение",
                "GPU training, mixed precision, distributed training basics, profiling, reproducibility",
            ),
        ],
    ),
    (
        "3. Production ML",
        "Linux и Docker",
        [
            (
                "Linux для диагностики",
                "filesystem, processes, signals, permissions, env, networking, bash, ssh, logs, CPU/RAM/disk",
            ),
            (
                "Контейнеризация",
                "Dockerfile, images/containers, volumes, networks, multi-stage builds, Docker Compose, optimization",
            ),
        ],
    ),
    (
        "3. Production ML",
        "Базы данных и поиск",
        [
            ("PostgreSQL и транзакции", "indexes, ACID, isolation levels, transactions, query planning"),
            ("NoSQL и кэш", "Redis, document databases, key-value stores; consistency и trade-offs"),
            (
                "Векторный и полнотекстовый поиск",
                "FAISS, pgvector, Elasticsearch/OpenSearch, vector DB, exact vs approximate search",
            ),
        ],
    ),
    (
        "3. Production ML",
        "Backend для ML",
        [
            (
                "API предсказаний",
                "HTTP, REST, API design, FastAPI, serialization, client → preprocessing → model → response",
            ),
            (
                "Нагрузка и обмен сообщениями",
                "async, queues, caching, WebSockets, gRPC, timeouts, retries, backpressure",
            ),
            (
                "Контракты и защита API",
                "authentication basics, validation, versioning, idempotency, error handling",
            ),
        ],
    ),
    (
        "3. Production ML",
        "Техническая документация",
        [
            (
                "README, RFC и ADR",
                "README, design docs, RFC, Architecture Decision Records, API documentation, trade-offs",
            ),
            (
                "Отчёты и postmortem",
                "experiment reports, postmortems: факты, причины, меры, без поиска виноватых",
            ),
        ],
    ),
    (
        "3. Production ML",
        "Data Engineering",
        [
            (
                "Надёжные data pipelines",
                "ETL/ELT, batch, warehouse/lake/lakehouse, schema evolution, data quality, idempotency",
            ),
            ("Streaming и оркестрация", "Kafka, Spark, Airflow, event time, late data, retries, backfills"),
        ],
    ),
    (
        "3. Production ML",
        "MLOps",
        [
            (
                "Воспроизводимые эксперименты",
                "experiment tracking, MLflow, model registry, dataset versioning, DVC, reproducibility",
            ),
            (
                "Пайплайн обучения",
                "pipelines, orchestration, Airflow/Dagster/Prefect, Kubeflow, feature stores, Feast, training-serving skew",
            ),
            ("Доставка модели", "model serving, batch/online inference, shadow/canary, A/B, rollback"),
            (
                "Цикл переобучения",
                "data → training → validation → registry → deployment → monitoring → retraining, quality gates",
            ),
        ],
    ),
    (
        "3. Production ML",
        "Cloud",
        [
            (
                "Облачные компоненты",
                "AWS/GCP/Azure на примере одного: compute, object storage, databases, containers, networking",
            ),
            ("Эксплуатация в облаке", "IAM, secrets, monitoring, autoscaling, зоны отказа, бюджет"),
        ],
    ),
    (
        "3. Production ML",
        "Kubernetes",
        [
            ("Базовые объекты", "Pod, Deployment, Service, ConfigMap, Secret, Ingress"),
            (
                "Надёжный deployment",
                "requests/limits, autoscaling, health checks, rolling deployment, graceful shutdown",
            ),
        ],
    ),
    (
        "3. Production ML",
        "Мониторинг ML",
        [
            ("Наблюдаемость сервиса", "latency, throughput, error rate, CPU/GPU utilization, alerting, SLO"),
            (
                "Качество после релиза",
                "model metrics, delayed labels, feature distributions, data/concept/prediction drift, data quality",
            ),
        ],
    ),
    (
        "4. Уровень Senior",
        "Ownership",
        [
            (
                "Ответственность за результат",
                "от требований до production, взаимодействие с data/backend/product, мониторинг, rollback, инциденты",
            )
        ],
    ),
    (
        "4. Уровень Senior",
        "System Design",
        [
            (
                "Основы распределённых систем",
                "latency, throughput, scalability, availability, consistency, caching, queues, batch/streaming, storage, failure handling, observability, cost",
            ),
            (
                "Рекомендательная система",
                "events → Kafka → feature pipeline/store → candidate generation → ranking → API; cold start",
            ),
            (
                "Поиск и рекламное ранжирование",
                "search/ranking, ad ranking, retrieval, online/offline metrics, experiments",
            ),
            (
                "Fraud, spam и аномалии",
                "fraud detection, spam detection, anomaly detection, class imbalance, delayed labels, adversarial drift",
            ),
            (
                "Churn от идеи до эксплуатации",
                "churn prediction, actionable intervention, batch scoring, causal effect, cost, end-to-end design",
            ),
        ],
    ),
    (
        "4. Уровень Senior",
        "Производительность",
        [
            (
                "Поиск узкого места",
                "CPU/GPU, RAM/VRAM, I/O, vectorization, batching, concurrency, multiprocessing, caching, profiling",
            ),
            (
                "Оптимизация inference",
                "latency/throughput, batch size, quantization, ONNX, TensorRT, model compression, quality regression",
            ),
        ],
    ),
    (
        "4. Уровень Senior",
        "Безопасность",
        [
            (
                "Данные и доступ",
                "authentication/authorization, secrets, IAM, encryption, PII, data/model access controls",
            ),
            (
                "Защита ML-сервиса",
                "dependency vulnerabilities, API security, supply chain, abuse, prompt injection для LLM",
            ),
        ],
    ),
    (
        "4. Уровень Senior",
        "Стоимость",
        [
            (
                "Экономика ML-системы",
                "training, GPU inference, storage, network, databases, LLM API, autoscaling; quality/latency/cost/complexity",
            )
        ],
    ),
    (
        "4. Уровень Senior",
        "Принятие решений",
        [
            (
                "Аргументировать trade-offs",
                "LightGBM vs NN, batch vs real-time, pgvector vs vector DB, external API vs own serving; обратимость решений",
            )
        ],
    ),
    (
        "4. Уровень Senior",
        "Приоритизация",
        [
            (
                "Выбирать работу с максимальной пользой",
                "must-have/nice-to-have, impact/effort, accuracy vs latency, риск, короткие эксперименты",
            )
        ],
    ),
    (
        "4. Уровень Senior",
        "Работа с неопределённостью",
        [
            (
                "Расследовать размытую проблему",
                "рекомендации стали хуже: гипотезы, данные, проверка, ограничения, decision log, критерии остановки",
            )
        ],
    ),
    (
        "4. Уровень Senior",
        "Code Review",
        [
            (
                "Ревью инженерных решений",
                "correctness, readability, maintainability, coupling, architecture, performance, reliability; конструктивная обратная связь",
            )
        ],
    ),
    (
        "4. Уровень Senior",
        "Менторинг",
        [
            (
                "Развивать самостоятельность коллег",
                "объяснение решений, code review, декомпозиция, совместный debugging, engineering practices, обратная связь",
            )
        ],
    ),
    (
        "5. Специализация LLM",
        "Transformers и LLM",
        [
            (
                "Как устроен Transformer",
                "tokenization, embeddings, positional encoding, self/multi-head attention, encoder/decoder, context windows",
            ),
            (
                "Обучение и адаптация LLM",
                "pretraining, instruction tuning, SFT, LoRA/PEFT; fine-tuning vs RAG",
            ),
            ("Serving LLM", "inference, quantization, KV cache, batching, context windows, latency, memory"),
            (
                "LLM-приложения и агенты",
                "prompting, structured outputs, tool/function calling, agents, границы полномочий",
            ),
            ("RAG и поиск", "embeddings, semantic search, chunking, reranking, vector DB, hybrid search"),
            (
                "Оценка и ограничения LLM",
                "LLM evaluation, hallucination mitigation, guardrails, prompt injection, regression datasets",
            ),
            (
                "Проектирование LLM/RAG-сервиса",
                "end-to-end architecture, качество/стоимость/задержки, нужен ли LLM или достаточно ML/поиска/правил",
            ),
        ],
    ),
]

TOPICS = tuple(
    Topic(
        i,
        stage,
        title,
        tuple(Lesson(f"{i:02d}.{j:02d}", i, name, scope) for j, (name, scope) in enumerate(sections, 1)),
    )
    for i, (stage, title, sections) in enumerate(CATALOG, 1)
)
LESSONS = {lesson.id: lesson for topic in TOPICS for lesson in topic.lessons}


def aggregate_status(statuses: list[str]) -> str:
    if statuses and all(s == "passed" for s in statuses):
        return "passed"
    return "failed" if "failed" in statuses else "not_started"
