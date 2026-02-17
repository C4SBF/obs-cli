"""Tests for CLI argument parsing."""

import pytest

from obs_cli.main import create_parser, detect_output_format


def test_scan_command_with_defaults():
    """Test scan command uses correct defaults."""
    # Given
    parser = create_parser()

    # When
    args = parser.parse_args(["scan", "-o", "output.yaml"])

    # Then
    assert args.command == "scan"
    assert args.network is None
    assert args.output == "output.yaml"
    assert args.format is None
    assert args.verbose is False


def test_scan_command_with_custom_args():
    """Test scan command accepts custom arguments."""
    # Given
    parser = create_parser()

    # When
    args = parser.parse_args(
        [
            "scan",
            "--network",
            "10.0.0.0/16",
            "--output",
            "result.json",
            "--format",
            "json",
        ]
    )

    # Then
    assert args.network == "10.0.0.0/16"
    assert args.output == "result.json"
    assert args.format == "json"


def test_discover_command_with_defaults():
    """Test discover command uses correct defaults."""
    # Given
    parser = create_parser()

    # When
    args = parser.parse_args(["discover", "-o", "output.yaml"])

    # Then
    assert args.command == "discover"
    assert args.network is None
    assert args.max_concurrent == 10
    assert args.output == "output.yaml"


def test_discover_command_with_custom_args():
    """Test discover command accepts custom arguments."""
    # Given
    parser = create_parser()

    # When
    args = parser.parse_args(
        [
            "discover",
            "-n",
            "172.16.0.0/24",
            "-c",
            "5",
            "-o",
            "discovery.yaml",
        ]
    )

    # Then
    assert args.network == "172.16.0.0/24"
    assert args.max_concurrent == 5
    assert args.output == "discovery.yaml"


def test_classify_command_with_defaults():
    """Test classify command uses correct defaults."""
    # Given
    parser = create_parser()

    # When
    args = parser.parse_args(
        [
            "classify",
            "--input",
            "discovery.yaml",
            "--output",
            "classified.yaml",
        ]
    )

    # Then
    assert args.command == "classify"
    assert args.input == "discovery.yaml"
    assert args.output == "classified.yaml"
    assert "brickschema.org" in args.topology_url


def test_missing_output_raises_error():
    """Test that missing output argument raises SystemExit."""
    # Given
    parser = create_parser()

    # When/Then
    with pytest.raises(SystemExit):
        parser.parse_args(["scan"])


def test_missing_command_raises_error():
    """Test that missing command raises SystemExit."""
    # Given
    parser = create_parser()

    # When/Then
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_detect_output_format_yaml():
    """Test YAML format detection from file extension."""
    # Given
    yaml_paths = ["output.yaml", "output.yml", "result.YAML"]

    # When/Then
    for path in yaml_paths:
        assert detect_output_format(path) == "yaml"


def test_detect_output_format_json():
    """Test JSON format detection from file extension."""
    # Given
    path = "output.json"

    # When
    result = detect_output_format(path)

    # Then
    assert result == "json"


def test_detect_output_format_defaults_to_yaml():
    """Test that unknown extensions default to YAML format."""
    # Given
    path = "output.txt"

    # When
    result = detect_output_format(path)

    # Then
    assert result == "yaml"
