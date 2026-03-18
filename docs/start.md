# 项目预处理与翻译流程指南

## 阶段一：项目预处理

### 1.1 添加 <project> JAR 插件

**命令：**

```bash
bash scripts/java/add_plugin.sh <project>
```

- **作用：** 将 `<project>-jar-plugin` 添加到项目的 `pom.xml`，用于生成测试 JAR。
- **生成文件：** `projects/java/automated_reduced_projects/<project>/` 目录（从 `original_projects` 复制并添加插件）。

------

### 1.2 构建项目并合并 JAR

**命令：**

```bash
bash scripts/java/merge_jar.sh <project>
```

- **作用：** 执行 `mvn clean install` 构建项目，将主代码和测试代码合并成单个 JAR。
- **依赖：** 需要 Java 和 <project> 环境。
- **生成文件：**
  - `projects/java/automated_reduced_projects/<project>/target/*.jar` (主 JAR)
  - `projects/java/automated_reduced_projects/<project>/target/*-tests.jar` (测试 JAR)
  - `projects/java/automated_reduced_projects/<project>/target/*-merged.jar` (合并后的 JAR)

------

### 1.3 生成调用图

**命令：**

```Bash
bash scripts/java/generate_cg.sh <project>
```

- **作用：** 使用 `JavaCallgraph` 工具生成项目的调用图。
- **依赖：** `misc/java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar`
- **生成文件：** `projects/java/automated_reduced_projects/<project>/callgraph.txt`

------

### 1.4 缩减第三方依赖

**命令：**

```Bash
bash scripts/java/reduce_third_party_libs.sh <project>
cp projects/java/automated_reduced_projects/<project> projects/java/cleaned_final_projects/<project>
```

- **作用：** 分析调用图，移除未使用的第三方依赖，只保留项目自身的代码。
- **输入：** `callgraph.txt` 和原始项目。
- **生成文件：** `projects/java/automated_reduced_projects/<project>/` (更新后的项目)。

------

### 1.5 测试分解

测试分解分为两步：

**第一步：提取测试覆盖率**

```Bash
bash scripts/java/extract_coverage.sh <project> ''
```

- **作用：** 执行测试并提取覆盖率信息。
- **生成文件：** `data/java/source_test_execution/` 目录。
- **注意：** 运行脚本前需要进行测试: *`mvn test`*,并添加 *`jacoco`* 插件

**第二步：分解测试**

```Bash
bash scripts/java/decompose_test.sh <project>
```

- **作用：** 将测试分解为独立片段，解决长调用链问题。
- **生成文件：** `projects/java/cleaned_final_projects_decomposed_tests/<project>/`
- **注意：** 测试分解后可能需要手动调整，如移除 `@Test(expected = ...)` 注解。

------

## 阶段二：CodeQL 分析与翻译

### 1.1 创建 CodeQL 数据库

**命令：**

```Bash
bash scripts/java/create_database.sh <project> "_decomposed_tests"
```

- **作用：** 为预处理后的项目创建 CodeQL 数据库。
- **生成文件：** `databases/<project>_decomposed_tests/`
- **注意：** 此脚本只处理固定的 10 个项目列表，需要手动修改或为 `<project>` 创建单独版本。

------

### 2.2 执行 CodeQL 查询

**命令：**

```Bash
bash scripts/java/create_query_outputs.sh <project> "_decomposed_tests"  
```

- **作用：** 运行 CodeQL 查询，提取类型、方法调用等信息。
- **生成文件：** `data/java/query_outputs_decomposed_tests/`

------

### 2.3 创建项目架构

**命令：**

```Bash
bash scripts/java/create_schema.sh <project> <suffix>
bash scripts/java/extract_call_graph.sh <project> <suffix>
```

- **作用：** 根据 CodeQL 查询结果创建项目 schema（JSON 格式）。
- **生成文件：** `data/java/schemas_decomposed_tests/<project>/`

------

### 2.4 类型翻译

**命令：**
```Bash
bash scripts/java/extract_types.sh <project> <suffix>
bash scripts/java/crawl_type_desc.sh <project> <suffix>
bash scripts/java/translate_types.sh <project> <model_name> <type>
```

------

### 2.5 生成骨架结构

**命令：**

```Bash
bash scripts/java/get_dependencies.sh <project> <suffix>
bash scripts/java/create_skeleton.sh <project> <model> <type> <suffix> <temperature>
```

- **作用：** 在目标语言中 `data/java/skeletons/<project_name>` 下创建合适的骨架（语法正确的空实现）。
- **生成文件：** 更新到 `data/java/skeletons/<project_name>`。

------

### 2.5 翻译

**命令：**

```Bash
bash scripts/java/generate_test_invocation_map.sh <project> <model> <suffix>
bash scripts/java/extract_coverage.sh <project> <suffix>
```

- **作用：** 提取测试覆盖率，用于指导翻译。
- **生成文件：** `data/java/source_test_execution/`

------

### 2.6 执行翻译

**命令：**

```Bash
bash scripts/java/translate_fragment.sh <project> gpt-4o-2024-11-20 0.0
```

- **作用：** 调用 LLM 翻译代码片段，按反向调用图顺序执行。
- **参数：**
  - `<project>` - 项目名
  - `0.0` - temperature
  - `gpt-4o-2024-11-20` - 模型名
- **依赖：** `configs/model_configs.yaml` 中配置了 API。
- **生成文件：** `data/java/schemas_decomposed_tests/translations/<project>/` (JSON 格式翻译结果)。

------

### 2.7 查看翻译结果

**命令：**

```Bash
bash scripts/java/print_results.sh <project> 0.0 gpt-4o-2024-11-20 data/java/schemas_decomposed_tests/translations
```

- **作用：** 打印翻译结果统计（语法正确性、GraalVM 正确性、测试通过率等）。

------

### 2.8 重组为独立 Python 项目

**命令：**

```Bash
bash scripts/java/recompose.sh <project> 0.0 gpt-4o-2024-11-20
```

- **作用：** 将翻译片段组合成独立的 Python 项目。
- **生成文件：** `data/java/schemas_decomposed_tests/translations/<project>_python/`

------

## 说明

1. **手动调整：** 测试分解后可能需要手动调整，确保 <project> 能编译。
2. **模型配置：** 翻译需要配置 LLM API，当前 `configs/model_configs.yaml` 已配置 `gpt-4o-2024-11-20`。
3. **中途可能需要重新运行测试代码:** `cd /home/AlphaTrans/projects/java/cleaned_final_projects_decomposed_tests/<project> && mvn clean test -Drat.skip=true`

