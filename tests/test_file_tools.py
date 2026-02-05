"""Tests for file operation tools"""
from iribot.tools.read_file import ReadFileTool
from iribot.tools.write_file import WriteFileTool
from iribot.tools.list_directory import ListDirectoryTool


class TestReadFileTool:
    """Test ReadFileTool functionality"""

    def test_read_existing_file(self, tmp_path):
        """Test reading an existing file"""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = "This is a test file\nWith multiple lines"
        test_file.write_text(test_content)

        # Test reading
        tool = ReadFileTool()
        result = tool.execute(file_path=str(test_file))

        assert result["success"] is True
        assert result["content"] == test_content

    def test_read_nonexistent_file(self, tmp_path):
        """Test reading a file that doesn't exist"""
        nonexistent = str(tmp_path / "nonexistent.txt")

        tool = ReadFileTool()
        result = tool.execute(file_path=nonexistent)

        assert result["success"] is False
        assert "error" in result or "not found" in str(result).lower()

    def test_read_file_with_encoding(self, tmp_path):
        """Test reading file with UTF-8 content"""
        test_file = tmp_path / "utf8.txt"
        test_content = "Hello 世界 مرحبا мир"
        test_file.write_text(test_content, encoding="utf-8")

        tool = ReadFileTool()
        result = tool.execute(file_path=str(test_file))

        assert result["success"] is True
        assert "世界" in result["content"]


class TestWriteFileTool:
    """Test WriteFileTool functionality"""

    def test_write_new_file(self, tmp_path):
        """Test writing to a new file"""
        test_file = tmp_path / "new_file.txt"
        test_content = "This is new content"

        tool = WriteFileTool()
        result = tool.execute(file_path=str(test_file), content=test_content)

        assert result["success"] is True
        assert test_file.read_text() == test_content

    def test_overwrite_existing_file(self, tmp_path):
        """Test overwriting an existing file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Old content")

        new_content = "New content"
        tool = WriteFileTool()
        result = tool.execute(file_path=str(test_file), content=new_content)

        assert result["success"] is True
        assert test_file.read_text() == new_content

    def test_write_file_with_utf8(self, tmp_path):
        """Test writing UTF-8 content"""
        test_file = tmp_path / "utf8.txt"
        test_content = "Unicode: 中文 العربية Русский"

        tool = WriteFileTool()
        result = tool.execute(file_path=str(test_file), content=test_content)

        assert result["success"] is True
        assert test_content in test_file.read_text(encoding="utf-8")

    def test_write_file_creates_directories(self, tmp_path):
        """Test that write tool creates necessary directories"""
        test_file = tmp_path / "subdir" / "nested" / "file.txt"
        test_content = "Content in nested directory"

        tool = WriteFileTool()
        result = tool.execute(file_path=str(test_file), content=test_content)

        assert result["success"] is True
        assert test_file.read_text() == test_content


class TestListDirectoryTool:
    """Test ListDirectoryTool functionality"""

    def test_list_empty_directory(self, tmp_path):
        """Test listing an empty directory"""
        tool = ListDirectoryTool()
        result = tool.execute(path=str(tmp_path))

        assert result["success"] is True
        assert result["items"] == []

    def test_list_directory_with_files(self, tmp_path):
        """Test listing directory with files"""
        # Create some files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()

        tool = ListDirectoryTool()
        result = tool.execute(path=str(tmp_path))

        assert result["success"] is True
        assert len(result["items"]) == 3
        item_names = [item["name"] for item in result["items"]]
        assert "file1.txt" in item_names
        assert "file2.txt" in item_names
        assert "subdir" in item_names

    def test_list_nonexistent_directory(self):
        """Test listing a directory that doesn't exist"""
        tool = ListDirectoryTool()
        result = tool.execute(path="/nonexistent/path/to/dir")

        assert result["success"] is False

    def test_list_directory_shows_type(self, tmp_path):
        """Test that list shows whether items are files or directories"""
        (tmp_path / "file.txt").write_text("content")
        (tmp_path / "subdir").mkdir()

        tool = ListDirectoryTool()
        result = tool.execute(path=str(tmp_path))

        assert result["success"] is True
        items_dict = {item["name"]: item for item in result["items"]}

        assert items_dict["file.txt"]["type"] == "file"
        assert items_dict["subdir"]["type"] == "directory"


class TestFileToolsIntegration:
    """Test integration between file tools"""

    def test_write_and_read_file(self, tmp_path):
        """Test writing a file and reading it back"""
        test_file = tmp_path / "integration_test.txt"
        test_content = """Line 1
Line 2
Line 3 with special chars: !@#$%^&*()"""

        # Write file
        write_tool = WriteFileTool()
        write_result = write_tool.execute(
            file_path=str(test_file), content=test_content
        )
        assert write_result["success"] is True

        # Read file back
        read_tool = ReadFileTool()
        read_result = read_tool.execute(file_path=str(test_file))
        assert read_result["success"] is True
        assert read_result["content"] == test_content

    def test_list_and_read_files(self, tmp_path):
        """Test listing directory and reading files from it"""
        # Create files
        files = {
            "file1.txt": "Content 1",
            "file2.txt": "Content 2",
            "file3.txt": "Content 3",
        }

        for filename, content in files.items():
            (tmp_path / filename).write_text(content)

        # List directory
        list_tool = ListDirectoryTool()
        list_result = list_tool.execute(path=str(tmp_path))
        assert list_result["success"] is True

        # Read each file
        read_tool = ReadFileTool()
        for item in list_result["items"]:
            if item["type"] == "file":
                result = read_tool.execute(file_path=str(tmp_path / item["name"]))
                assert result["success"] is True
                assert result["content"] in files.values()
