"""Testes do pipeline de processamento (funções puras, sem banco)."""
import pandas as pd
import pytest

from app.processing import (
    _normalize_emails,
    _normalize_phone,
    _normalize_phones_field,
    _normalize_col_name,
    _find_column_mapping,
    process_to_ghl,
    GHL_COLUMNS,
)


class TestNormalizeEmails:
    def test_single_email(self):
        assert _normalize_emails("User@Example.COM") == "user@example.com"

    def test_multiple_emails_comma(self):
        result = _normalize_emails("a@b.com, c@d.com")
        assert result == "a@b.com, c@d.com"

    def test_multiple_emails_semicolon(self):
        result = _normalize_emails("a@b.com;c@d.com")
        assert result == "a@b.com, c@d.com"

    def test_dedup(self):
        result = _normalize_emails("a@b.com, a@b.com, c@d.com")
        assert result == "a@b.com, c@d.com"

    def test_empty(self):
        assert _normalize_emails("") == ""
        assert _normalize_emails(None) == ""

    def test_invalid_no_at(self):
        assert _normalize_emails("not-an-email") == ""


class TestNormalizePhone:
    def test_brazilian_mobile(self):
        result = _normalize_phone("85999991234")
        assert result == "+5585999991234"

    def test_with_country_code(self):
        result = _normalize_phone("+5585999991234")
        assert result == "+5585999991234"

    def test_with_formatting(self):
        result = _normalize_phone("(85) 99999-1234")
        assert result == "+5585999991234"

    def test_empty(self):
        assert _normalize_phone("") == ""
        assert _normalize_phone(None) == ""


class TestNormalizePhonesField:
    def test_multiple_phones(self):
        result = _normalize_phones_field("85999991234;85988881234")
        assert "+5585999991234" in result
        assert "+5585988881234" in result

    def test_dedup(self):
        result = _normalize_phones_field("85999991234,85999991234")
        assert result.count("+5585999991234") == 1

    def test_empty(self):
        assert _normalize_phones_field("") == ""


class TestNormalizeColName:
    def test_lowercase(self):
        assert _normalize_col_name("Email") == "email"

    def test_strip_spaces(self):
        assert _normalize_col_name("  Nome  ") == "nome"

    def test_multiple_spaces(self):
        assert _normalize_col_name("Nome  Completo") == "nome completo"

    def test_empty(self):
        assert _normalize_col_name("") == ""
        assert _normalize_col_name(None) == ""


class TestFindColumnMapping:
    def test_maps_portuguese(self):
        df = pd.DataFrame(columns=["Nome", "Email", "Telefone", "Empresa"])
        mapping = _find_column_mapping(df)
        assert mapping["Full Name"] == "Nome"
        assert mapping["Email"] == "Email"
        assert mapping["Phone"] == "Telefone"
        assert mapping["Company Name"] == "Empresa"

    def test_maps_english(self):
        df = pd.DataFrame(columns=["Full Name", "Email", "Phone", "Company Name"])
        mapping = _find_column_mapping(df)
        assert mapping["Full Name"] == "Full Name"
        assert mapping["Email"] == "Email"
        assert mapping["Phone"] == "Phone"

    def test_unmapped_columns(self):
        df = pd.DataFrame(columns=["Nome", "CampoDesconhecido"])
        mapping = _find_column_mapping(df)
        assert mapping["Full Name"] == "Nome"
        assert mapping["Email"] is None


class TestProcessToGhl:
    def test_basic_conversion(self):
        df = pd.DataFrame({
            "Nome": ["João Silva"],
            "Email": ["joao@test.com"],
            "Telefone": ["85999991234"],
        })
        result = process_to_ghl(df)
        assert list(result.columns) == GHL_COLUMNS
        assert len(result) == 1
        assert result.iloc[0]["Full Name"] == "João Silva"
        assert result.iloc[0]["Email"] == "joao@test.com"
        assert result.iloc[0]["Phone"] == "+5585999991234"

    def test_unmapped_goes_to_notes(self):
        df = pd.DataFrame({
            "Nome": ["João"],
            "CPF": ["123.456.789-00"],
        })
        result = process_to_ghl(df)
        assert "CPF: 123.456.789-00" in result.iloc[0]["Notes"]

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["Nome", "Email"])
        result = process_to_ghl(df)
        assert len(result) == 0
        assert list(result.columns) == GHL_COLUMNS

    def test_all_ghl_columns_present(self):
        df = pd.DataFrame({"Nome": ["Test"]})
        result = process_to_ghl(df)
        for col in GHL_COLUMNS:
            assert col in result.columns
