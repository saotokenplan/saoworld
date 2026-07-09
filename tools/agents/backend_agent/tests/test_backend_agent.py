"""
Backend Agent 测试用例

测试 Backend Agent 的核心功能：分析设计文档、检查现有代码、实现数据模型、
实现数据访问层、实现 Pydantic Schemas、实现 API 路由、生成迁移脚本、
编写测试用例、运行测试验证、交付成果。
"""

import pytest
from ..backend_agent import BackendAgent
from ..backend_input_schemas import (
    BackendAgentInput,
    DataStructure,
    DesignTask,
    ExistingCode,
    FieldDefinition,
    APISpec,
)
from ..backend_error_handler import BackendErrorHandler


class TestBackendAgent:
    """Backend Agent 核心功能测试"""

    @pytest.fixture
    def agent(self) -> BackendAgent:
        """创建 Backend Agent 实例"""
        return BackendAgent()

    @pytest.fixture
    def design_task(self) -> DesignTask:
        """创建设计任务"""
        return DesignTask(
            design_id="DESIGN-001",
            task_id="TASK-001",
            title="新增区域创建接口",
            type="api",
            target_service="world-service",
            requirements=[
                "实现 POST /api/v1/world/regions",
                "实现 GET /api/v1/world/regions",
                "添加权限校验 world:read/world:write",
            ],
            priority="high",
        )

    @pytest.fixture
    def data_structure(self) -> DataStructure:
        """创建数据结构"""
        return DataStructure(
            model_name="Region",
            table_name="regions",
            fields=[
                FieldDefinition(
                    name="region_id",
                    type="UUID",
                    primary_key=True,
                    nullable=False,
                ),
                FieldDefinition(
                    name="name",
                    type="VARCHAR(255)",
                    nullable=False,
                    unique=True,
                ),
                FieldDefinition(
                    name="status",
                    type="VARCHAR(32)",
                    nullable=False,
                    check=["locked", "active", "unstable", "archived"],
                ),
                FieldDefinition(
                    name="created_at",
                    type="TIMESTAMPTZ",
                    nullable=False,
                    server_default="now()",
                ),
            ],
            constraints=[],
            indexes=[],
        )

    @pytest.fixture
    def existing_code(self) -> ExistingCode:
        """创建现有代码状态"""
        return ExistingCode(
            service_name="world-service",
            has_routes=True,
            has_models=True,
            has_repositories=True,
            has_schemas=True,
            has_tests=True,
            existing_models=["WorldSkeleton"],
            existing_routes=["/api/v1/world/skeleton"],
            test_count=20,
        )

    def test_agent_initialization(self, agent: BackendAgent) -> None:
        """测试 Backend Agent 初始化"""
        assert agent.current_step == 0
        assert agent.max_steps == 10
        assert len(agent.errors) == 0
        assert len(agent.warnings) == 0
        assert len(agent.files_modified) == 0

    def test_analyze_design_document(
        self, agent: BackendAgent, design_task: DesignTask
    ) -> None:
        """测试步骤 1：分析设计文档"""
        result = agent.analyze_design_document(design_task)

        assert agent.current_step == 1
        assert result["task_id"] == "TASK-001"
        assert result["target_service"] == "world-service"
        assert result["task_type"] == "api"
        assert result["requirements_count"] == 3
        assert result["has_data_model"] is False
        assert result["priority"] == "high"
        assert len(result["parsed_requirements"]) == 3

    def test_identify_requirement_type(self, agent: BackendAgent) -> None:
        """测试需求类型识别"""
        # API 类型
        assert agent._identify_requirement_type("实现 POST /api/v1/world/regions") == "api"
        assert agent._identify_requirement_type("实现 GET /api/v1/world/regions") == "api"

        # Model 类型
        assert agent._identify_requirement_type("创建 Region 模型") == "model"

        # Repository 类型
        assert agent._identify_requirement_type("实现 Region Repository") == "repository"

        # Schema 类型
        assert agent._identify_requirement_type("创建 Region Schema") == "schema"

        # Test 类型
        assert agent._identify_requirement_type("编写测试用例") == "test"

        # Auth 类型
        assert agent._identify_requirement_type("添加权限校验") == "auth"

    def test_check_existing_code(
        self, agent: BackendAgent, existing_code: ExistingCode
    ) -> None:
        """测试步骤 2：检查现有代码"""
        result = agent.check_existing_code(existing_code)

        assert agent.current_step == 2
        assert result["service_name"] == "world-service"
        assert result["has_routes"] is True
        assert result["has_models"] is True
        assert result["has_existing_code"] is True
        assert result["needs_full_setup"] is False
        assert len(result["existing_models"]) == 1

    def test_check_existing_code_none(self, agent: BackendAgent) -> None:
        """测试步骤 2：检查现有代码（无现有代码）"""
        result = agent.check_existing_code(None)

        assert result["service_name"] == "unknown"
        assert result["has_existing_code"] is False
        assert result["needs_full_setup"] is True

    def test_implement_data_model(
        self, agent: BackendAgent, data_structure: DataStructure
    ) -> None:
        """测试步骤 3：实现数据模型"""
        result = agent.implement_data_model(data_structure)

        assert agent.current_step == 3
        assert result["model_name"] == "Region"
        assert result["table_name"] == "regions"
        assert result["fields_count"] == 4
        assert result["file_path"] == "app/domain/models.py"
        assert "class Region(Base):" in result["model_code"]
        assert "__tablename__ = \"regions\"" in result["model_code"]
        assert len(agent.files_modified) == 1

    def test_generate_field_definition(self, agent: BackendAgent) -> None:
        """测试字段定义生成"""
        # 主键字段
        field = FieldDefinition(
            name="id",
            type="UUID",
            primary_key=True,
            nullable=False,
        )
        field_def = agent._generate_field_definition(field)
        assert "primary_key=True" in field_def
        assert "nullable=False" in field_def

        # 可空字段
        field = FieldDefinition(
            name="description",
            type="VARCHAR(255)",
            nullable=True,
        )
        field_def = agent._generate_field_definition(field)
        assert "Mapped[str]" in field_def

    def test_map_field_type(self, agent: BackendAgent) -> None:
        """测试字段类型映射"""
        assert agent._map_field_type("UUID") == "UUID"
        assert agent._map_field_type("VARCHAR(255)") == "str"
        assert agent._map_field_type("INTEGER") == "int"
        assert agent._map_field_type("BOOLEAN") == "bool"
        assert agent._map_field_type("TIMESTAMPTZ") == "datetime"
        assert agent._map_field_type("JSONB") == "dict[str, Any]"

    def test_implement_repository(self, agent: BackendAgent) -> None:
        """测试步骤 4：实现数据访问层"""
        result = agent.implement_repository("Region")

        assert agent.current_step == 4
        assert result["repository_name"] == "RegionRepository"
        assert result["file_path"] == "app/repositories/region_repo.py"
        assert "class RegionRepository:" in result["repository_code"]
        assert "async def get_by_id" in result["repository_code"]
        assert len(result["methods"]) == 5
        # 验证当前步骤添加了 1 个文件
        assert len(agent.files_modified) == 1

    def test_implement_schemas(
        self, agent: BackendAgent, data_structure: DataStructure
    ) -> None:
        """测试步骤 5：实现 Pydantic Schemas"""
        result = agent.implement_schemas("Region", data_structure.fields)

        assert agent.current_step == 5
        assert result["request_schema_name"] == "RegionRequest"
        assert result["response_schema_name"] == "RegionResponse"
        assert result["file_path"] == "app/schemas/region.py"
        assert "class RegionRequest(BaseModel):" in result["request_schema"]
        assert "class RegionResponse(BaseModel):" in result["response_schema"]
        # 验证当前步骤添加了 1 个文件
        assert len(agent.files_modified) == 1

    def test_implement_routes(self, agent: BackendAgent) -> None:
        """测试步骤 6：实现 API 路由"""
        api_spec = APISpec(
            endpoint="/api/v1/world/regions",
            method="POST",
            scope="world:write",
            request={"name": "RegionRequest", "fields": []},
            response={"name": "RegionResponse", "fields": []},
        )

        result = agent.implement_routes("world-service", [api_spec], "Region")

        assert agent.current_step == 6
        assert result["routes_count"] == 1
        assert result["file_path"] == "app/api/routes.py"
        assert "router = APIRouter" in result["routes_code"]
        assert "@router.post" in result["routes_code"]
        # 验证当前步骤添加了 1 个文件
        assert len(agent.files_modified) == 1

    def test_generate_migration(self, agent: BackendAgent) -> None:
        """测试步骤 7：生成迁移脚本"""
        result = agent.generate_migration("Region", "regions")

        assert agent.current_step == 7
        assert result["model_name"] == "Region"
        assert result["table_name"] == "regions"
        assert "alembic/versions/" in result["file_path"]
        assert "add_regions_table" in result["migration_name"]
        # 验证当前步骤添加了 1 个文件
        assert len(agent.files_modified) == 1

    def test_write_tests(self, agent: BackendAgent) -> None:
        """测试步骤 8：编写测试用例"""
        result = agent.write_tests("Region", "world-service")

        assert agent.current_step == 8
        assert result["test_file"] == "test_region.py"
        assert result["file_path"] == "tests/test_region.py"
        assert result["test_count"] == 5
        assert "class TestRegion:" in result["test_code"]
        assert "async def test_create_region" in result["test_code"]
        # 验证当前步骤添加了 1 个文件
        assert len(agent.files_modified) == 1

    def test_run_tests_and_verify(self, agent: BackendAgent) -> None:
        """测试步骤 9：运行测试验证"""
        result = agent.run_tests_and_verify("world-service")

        assert agent.current_step == 9
        assert result.service == "world-service"
        assert result.tests.passed == 5
        assert result.tests.failed == 0
        assert result.tests.total == 5
        assert result.lint.passed is True
        assert result.typecheck.passed is True

    def test_deliver_output(
        self, agent: BackendAgent, design_task: DesignTask
    ) -> None:
        """测试步骤 10：交付成果"""
        result = agent.deliver_output(design_task, "world-service")

        assert agent.current_step == 10
        assert result.design_id == "DESIGN-001"
        assert result.task_id == "TASK-001"
        assert result.service == "world-service"
        assert result.version == "1.0"
        assert result.status == "completed"
        # deliver_output 只返回当前 files_modified，不添加新文件
        assert len(result.files) >= 0

    def test_run_workflow(
        self,
        agent: BackendAgent,
        design_task: DesignTask,
        data_structure: DataStructure,
        existing_code: ExistingCode,
    ) -> None:
        """测试运行完整工作流"""
        input_data = BackendAgentInput(
            design_task=design_task,
            data_structures=[data_structure],
            existing_code=existing_code,
        )

        result = agent.run_workflow(input_data)

        assert result.success is True
        assert result.implementation.design_id == "DESIGN-001"
        assert result.implementation.service == "world-service"
        assert result.test_result is not None
        assert result.test_result.tests.passed == 5
        assert len(result.errors) == 0
        assert len(result.next_steps) == 2
        assert "已完成 world-service" in result.summary


class TestBackendErrorHandler:
    """Backend Agent 错误处理测试"""

    @pytest.fixture
    def error_handler(self) -> BackendErrorHandler:
        """创建错误处理器实例"""
        return BackendErrorHandler()

    def test_handle_design_incomplete(self, error_handler: BackendErrorHandler) -> None:
        """测试处理设计不完整错误"""
        error = error_handler.handle_design_incomplete(
            "需求列表为空", {"design_id": "DESIGN-001"}
        )

        assert "设计不完整" in error
        assert "需求列表为空" in error
        assert len(error_handler.error_log) == 1

    def test_handle_model_conflict(self, error_handler: BackendErrorHandler) -> None:
        """测试处理模型冲突"""
        error = error_handler.handle_model_conflict(
            "模型命名冲突", "Region", "Region"
        )

        assert "模型冲突" in error
        assert "Region" in error
        assert len(error_handler.error_log) == 1

    def test_handle_sqlalchemy_error(self, error_handler: BackendErrorHandler) -> None:
        """测试处理 SQLAlchemy 错误"""
        error = error_handler.handle_sqlalchemy_error(
            "模型定义错误", "class Region(Base):", "Invalid type mapping"
        )

        assert "SQLAlchemy 错误" in error
        assert "模型定义错误" in error
        assert len(error_handler.error_log) == 1

    def test_handle_test_failure(self, error_handler: BackendErrorHandler) -> None:
        """测试处理测试失败"""
        error = error_handler.handle_test_failure(
            "测试未通过", ["test_create_region"], "AssertionError: ..."
        )

        assert "测试失败" in error
        assert "test_create_region" in error
        assert len(error_handler.error_log) == 1

    def test_handle_type_check_failure(self, error_handler: BackendErrorHandler) -> None:
        """测试处理类型检查失败"""
        error = error_handler.handle_type_check_failure(
            "类型检查未通过", ["error: Incompatible types"]
        )

        assert "类型检查失败" in error
        assert len(error_handler.error_log) == 1

    def test_get_error_summary(self, error_handler: BackendErrorHandler) -> None:
        """测试获取错误摘要"""
        error_handler.handle_design_incomplete("错误1", {})
        error_handler.handle_test_failure("错误2", [], "")

        summary = error_handler.get_error_summary()

        assert summary["total_errors"] == 2
        assert "design_incomplete" in summary["error_types"]
        assert "test_failure" in summary["error_types"]

    def test_clear_errors(self, error_handler: BackendErrorHandler) -> None:
        """测试清空错误日志"""
        error_handler.handle_design_incomplete("错误", {})
        assert len(error_handler.error_log) == 1

        error_handler.clear_errors()
        assert len(error_handler.error_log) == 0

    def test_log_warning(self, error_handler: BackendErrorHandler) -> None:
        """测试记录警告"""
        warning = error_handler.log_warning("警告信息", {})

        assert "警告" in warning
        assert "警告信息" in warning
        assert len(error_handler.error_log) == 1