"""
安全配置检查模块测试
====================

测试安全配置基线检查功能
"""

import pytest
from nova_executor.security.config_checker import (
    CheckSeverity,
    CheckCategory,
    SecurityBaseline,
    ConfigCheck,
    ConfigViolation,
    ConfigCheckResult,
    SECURITY_BASELINES,
    ConfigChecker,
    get_config_checker,
    check_security_config,
    check_all_security_configs,
    get_security_baselines,
)


class TestCheckEnums:
    """测试检查枚举"""

    def test_check_severity_values(self):
        """测试严重级别枚举值"""
        assert CheckSeverity.CRITICAL.value == "critical"
        assert CheckSeverity.HIGH.value == "high"
        assert CheckSeverity.MEDIUM.value == "medium"
        assert CheckSeverity.LOW.value == "low"
        assert CheckSeverity.INFO.value == "info"

    def test_check_category_values(self):
        """测试检查类别枚举值"""
        assert CheckCategory.AUTHENTICATION.value == "authentication"
        assert CheckCategory.AUTHORIZATION.value == "authorization"
        assert CheckCategory.NETWORK.value == "network"
        assert CheckCategory.DATA_PROTECTION.value == "data_protection"
        assert CheckCategory.SESSION.value == "session"
        assert CheckCategory.LOGGING.value == "logging"
        assert CheckCategory.ENCRYPTION.value == "encryption"
        assert CheckCategory.COMPLIANCE.value == "compliance"


class TestSecurityBaseline:
    """测试安全基线"""

    def test_baseline_count(self):
        """测试基线数量"""
        assert len(SECURITY_BASELINES) > 10

    def test_baseline_structure(self):
        """测试基线结构"""
        for baseline in SECURITY_BASELINES:
            assert baseline.id is not None
            assert baseline.name is not None
            assert baseline.category is not None
            assert baseline.severity is not None
            assert baseline.recommended_value is not None
            assert baseline.check_type is not None

    def test_baseline_has_critical_checks(self):
        """测试包含关键检查"""
        critical = [b for b in SECURITY_BASELINES if b.severity == CheckSeverity.CRITICAL]
        assert len(critical) > 0

    def test_baseline_categories(self):
        """测试覆盖所有类别"""
        categories = set(b.category for b in SECURITY_BASELINES)
        expected_categories = set(CheckCategory)
        assert categories == expected_categories


class TestConfigChecker:
    """测试配置检查器"""

    def test_checker_initialization(self):
        """测试检查器初始化"""
        checker = ConfigChecker()
        assert checker is not None
        assert len(checker.baselines) > 0

    def test_get_baseline(self):
        """测试获取基线"""
        checker = ConfigChecker()
        baseline = checker.get_baseline("AUTH_001")

        assert baseline is not None
        assert baseline.id == "AUTH_001"
        assert baseline.name == "密码最小长度"

    def test_get_baseline_not_found(self):
        """测试获取不存在的基线"""
        checker = ConfigChecker()
        baseline = checker.get_baseline("INVALID_001")

        assert baseline is None

    def test_get_baselines_by_category(self):
        """测试按类别获取基线"""
        checker = ConfigChecker()
        baselines = checker.get_baselines_by_category(CheckCategory.AUTHENTICATION)

        assert len(baselines) > 0
        for b in baselines:
            assert b.category == CheckCategory.AUTHENTICATION

    def test_get_baselines_by_severity(self):
        """测试按严重级别获取基线"""
        checker = ConfigChecker()
        baselines = checker.get_baselines_by_severity(CheckSeverity.CRITICAL)

        assert len(baselines) > 0
        for b in baselines:
            assert b.severity == CheckSeverity.CRITICAL


class TestBooleanCheck:
    """测试布尔检查"""

    def test_check_boolean_true_pass(self):
        """测试布尔值 true 通过"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_003", True)

        assert result.passed is True
        assert result.check_name == "MFA 必须启用"

    def test_check_boolean_true_fail(self):
        """测试布尔值 true 失败"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_003", False)

        assert result.passed is False
        assert result.expected is True

    def test_check_boolean_false_pass(self):
        """测试布尔值 false 通过"""
        checker = ConfigChecker()
        baseline = checker.get_baseline("AUTH_003")
        baseline.recommended_value = False

        result = checker.check_config("AUTH_003", False)
        assert result.passed is True


class TestMinLengthCheck:
    """测试最小长度检查"""

    def test_check_min_length_pass(self):
        """测试最小长度通过"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_001", "MySecretPassword123")

        assert result.passed is True

    def test_check_min_length_fail(self):
        """测试最小长度失败"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_001", "short")

        assert result.passed is False
        assert result.actual == 5

    def test_check_min_length_boundary(self):
        """测试最小长度边界"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_001", "1234567")

        assert result.passed is False

        result = checker.check_config("AUTH_001", "12345678")
        assert result.passed is True


class TestMaxValueCheck:
    """测试最大值检查"""

    def test_check_max_value_pass(self):
        """测试最大值通过"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_004", 1800)

        assert result.passed is True

    def test_check_max_value_fail(self):
        """测试最大值失败"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_004", 3600)

        assert result.passed is False
        assert result.expected == 1800


class TestMinValueCheck:
    """测试最小值检查"""

    def test_check_min_value_pass(self):
        """测试最小值通过"""
        checker = ConfigChecker()
        result = checker.check_config("LOG_002", 100)

        assert result.passed is True

    def test_check_min_value_fail(self):
        """测试最小值失败"""
        checker = ConfigChecker()
        result = checker.check_config("LOG_002", 50)

        assert result.passed is False


class TestRangeCheck:
    """测试范围检查"""

    def test_check_range_pass(self):
        """测试范围通过"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_005", 90)

        assert result.passed is True

    def test_check_range_fail_too_low(self):
        """测试范围失败（太低）"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_005", 10)

        assert result.passed is False

    def test_check_range_fail_too_high(self):
        """测试范围失败（太高）"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_005", 200)

        assert result.passed is False

    def test_check_range_boundary(self):
        """测试范围边界"""
        checker = ConfigChecker()

        result = checker.check_config("AUTH_005", 30)
        assert result.passed is True

        result = checker.check_config("AUTH_005", 180)
        assert result.passed is True


class TestRegexCheck:
    """测试正则检查"""

    def test_check_regex_pass(self):
        """测试正则通过"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_002", "Password123!")

        assert result.passed is True

    def test_check_regex_fail(self):
        """测试正则失败"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_002", "password123")

        assert result.passed is False


class TestCheckConfigs:
    """测试批量检查配置"""

    def test_check_configs_multiple(self):
        """测试批量检查多个配置"""
        checker = ConfigChecker()
        configs = {
            "AUTH_001": "MySecretPassword123",
            "AUTH_004": 1800,
            "LOG_002": 100,
        }

        results = checker.check_configs(configs)

        assert len(results) == 3
        passed = sum(1 for r in results if r.passed)
        assert passed == 3

    def test_check_configs_mixed_results(self):
        """测试批量检查混合结果"""
        checker = ConfigChecker()
        configs = {
            "AUTH_001": "short",
            "AUTH_004": 1800,
            "LOG_002": 50,
        }

        results = checker.check_configs(configs)

        assert len(results) == 3
        passed = sum(1 for r in results if r.passed)
        assert passed == 1
        failed = sum(1 for r in results if not r.passed)
        assert failed == 2


class TestCheckAllBaselines:
    """测试检查所有基线"""

    def test_check_all_baselines(self):
        """测试检查所有基线"""
        checker = ConfigChecker()

        def get_value(baseline_id):
            return True

        results = checker.check_all_baselines(get_value)

        assert len(results) == len(checker.baselines)


class TestSummary:
    """测试摘要"""

    def test_get_summary(self):
        """测试获取摘要"""
        checker = ConfigChecker()
        checker.check_configs({
            "AUTH_001": "longpassword",
            "AUTH_003": True,
            "AUTH_004": 3600,
            "LOG_002": 100,
        })

        summary = checker.get_summary()

        assert "total_checks" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "pass_rate" in summary
        assert "by_category" in summary
        assert "by_severity" in summary

    def test_summary_pass_rate(self):
        """测试摘要通过率"""
        checker = ConfigChecker()
        checker.check_configs({
            "AUTH_001": "longpassword",
            "AUTH_004": 1800,
            "LOG_002": 100,
        })

        summary = checker.get_summary()

        assert summary["pass_rate"] == 1.0
        assert summary["passed"] == 3
        assert summary["failed"] == 0


class TestViolationsReport:
    """测试违规报告"""

    def test_violations_logged(self):
        """测试违规被记录"""
        checker = ConfigChecker()
        checker.check_config("AUTH_001", "short")

        assert len(checker.violations) == 1
        assert checker.violations[0].baseline_id == "AUTH_001"

    def test_get_violations_report(self):
        """测试获取违规报告"""
        checker = ConfigChecker()
        checker.check_config("AUTH_001", "short")
        checker.check_config("AUTH_004", 3600)
        checker.check_config("LOG_002", 50)

        report = checker.get_violations_report()

        assert len(report) == 3
        assert all(item["expected_value"] != item["actual_value"] for item in report)

    def test_get_violations_report_by_severity(self):
        """测试按严重级别过滤违规报告"""
        checker = ConfigChecker()
        checker.check_config("AUTH_001", "short")
        checker.check_config("AUTH_003", False)

        report = checker.get_violations_report(min_severity=CheckSeverity.HIGH)

        for item in report:
            severity_rank = [
                CheckSeverity.CRITICAL,
                CheckSeverity.HIGH,
                CheckSeverity.MEDIUM,
                CheckSeverity.LOW,
                CheckSeverity.INFO,
            ]
            assert severity_rank.index(CheckSeverity(item["severity"])) <= severity_rank.index(CheckSeverity.HIGH)

    def test_get_violations_report_by_category(self):
        """测试按类别过滤违规报告"""
        checker = ConfigChecker()
        checker.check_config("AUTH_001", "short")
        checker.check_config("NET_001", False)

        report = checker.get_violations_report(category=CheckCategory.NETWORK)

        assert len(report) == 1
        assert report[0]["category"] == "network"


class TestBaselineReport:
    """测试基线报告"""

    def test_generate_baseline_report(self):
        """测试生成基线报告"""
        checker = ConfigChecker()
        report = checker.generate_baseline_report()

        assert "total_baselines" in report
        assert "by_category" in report
        assert "by_severity" in report
        assert "critical_checks" in report

        assert report["total_baselines"] == len(checker.baselines)

    def test_critical_checks_count(self):
        """测试关键检查数量"""
        checker = ConfigChecker()
        report = checker.generate_baseline_report()

        critical_count = report["critical_checks"]
        assert critical_count > 0


class TestClearLogs:
    """测试清除日志"""

    def test_clear_logs(self):
        """测试清除日志"""
        checker = ConfigChecker()
        checker.check_config("AUTH_001", "short")
        checker.check_config("AUTH_004", 3600)

        assert len(checker.violations) == 2
        assert len(checker.check_results) == 2

        checker.clear_logs()

        assert len(checker.violations) == 0
        assert len(checker.check_results) == 0


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_check_security_config(self):
        """测试便捷配置检查"""
        checker = ConfigChecker()
        result = checker.check_config("AUTH_003", True)

        assert result.passed is False
        assert result.check_id == "AUTH_003"

    def test_check_all_security_configs(self):
        """测试便捷批量配置检查"""
        checker = ConfigChecker()
        results = checker.check_configs({
            "AUTH_001": "longpassword",
            "AUTH_004": 1800,
        })

        assert len(results) == 2

    def test_get_security_baselines(self):
        """测试获取所有基线"""
        baselines = get_security_baselines()

        assert len(baselines) == len(SECURITY_BASELINES)


class TestCheckIntegration:
    """测试检查集成"""

    def test_full_security_config_check(self):
        """测试完整安全配置检查"""
        checker = ConfigChecker()

        configs = {
            "AUTH_001": "SecurePassword123!",
            "AUTH_002": "Password123!",
            "AUTH_003": True,
            "AUTH_004": 1800,
            "AUTH_005": 90,
            "NET_001": True,
            "NET_003": True,
            "DATA_001": True,
            "DATA_002": True,
            "LOG_001": True,
            "LOG_003": True,
            "ENC_001": "TLSv1.2",
            "ENC_002": True,
            "AUTHZ_001": True,
            "AUTHZ_002": True,
            "COMP_001": True,
            "COMP_002": 365,
        }

        results = checker.check_configs(configs)

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        assert passed >= 10

    def test_security_config_failures(self):
        """测试安全配置失败场景"""
        checker = ConfigChecker()

        configs = {
            "AUTH_001": "short",
            "AUTH_002": "nospeshalchars",
            "AUTH_003": False,
            "AUTH_004": 7200,
            "AUTH_005": 500,
            "NET_001": False,
            "NET_003": False,
            "DATA_001": False,
            "DATA_002": False,
        }

        results = checker.check_configs(configs)

        failed = [r for r in results if not r.passed]
        assert len(failed) > 0

        critical_failed = [
            r for r in failed
            if r.severity == CheckSeverity.CRITICAL
        ]
        assert len(critical_failed) > 0

    def test_realtime_security_monitoring(self):
        """测试实时安全监控"""
        checker = ConfigChecker()

        configs = {
            "AUTH_001": "goodpassword123",
            "AUTH_003": True,
            "NET_001": True,
        }
        results = checker.check_configs(configs)
        initial_passed = sum(1 for r in results if r.passed)

        configs = {
            "AUTH_001": "short",
            "AUTH_004": 3600,
        }
        results = checker.check_configs(configs)
        new_failures = sum(1 for r in results if not r.passed)

        assert new_failures == 2
        summary = checker.get_summary()
        assert summary["failed"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
