SOME_CHANGES = "some changes"
SOME_OTHER_FILENAME = "SOME_OTHER_FILENAME.txt"
SOME_BRANCH_NAME = "some-branch-name"
SOME_OTHER_BRANCH_NAME = "some-other-branch-name"
SOME_CONTENT = "some-content"
SOME_MODIFY_FILE_DIFF = "diff --git a/foo.txt b/foo.txt\nindex 5f0c613..74cd6e7 100644\n--- a/foo.txt\n+++ b/foo.txt\n@@ -1 +1 @@\n-some changes\n\\ No newline at end of file\n+some-content\n\\ No newline at end of file"
SOME_DELETE_FILE_DIFF = "diff --git a/foo.txt b/foo.txt\ndeleted file mode 100644\nindex 5f0c613..0000000\n--- a/foo.txt\n+++ /dev/null\n@@ -1 +0,0 @@\n-some changes\n\\ No newline at end of file"
SOME_NEW_FILE_DIFF = "diff --git a/SOME_OTHER_FILENAME.txt b/SOME_OTHER_FILENAME.txt\nnew file mode 100644\nindex 0000000..e69de29"

def _delete_existing_file(local_repo: Repo, filename: str) -> None:
    test_second_file_path = Path(local_repo.working_dir) / filename
    test_second_file_path.unlink()


def _modify_existing_file(local_repo: Repo, filename: str, content: str) -> None:
    test_file_path = Path(local_repo.working_dir) / filename
    test_file_path.write_text(content)


def _add_new_file(local_repo: Repo, filename: str) -> None:
    test_other_file_path = Path(local_repo.working_dir) / filename
    test_other_file_path.touch()


@pytest.mark.parametrize(
    (
        "some_source_modifier",
        "some_source_modifier_inputs",
        "some_other_source_modifier",
        "some_other_source_modifier_inputs",
        "some_result",
        "some_other_result",
    ),
    [
        (
            _modify_existing_file,
            [SOME_CONTENT_FILENAME, SOME_CONTENT],
            _modify_existing_file,
            [SOME_CONTENT_FILENAME, SOME_CONTENT],
            SOME_MODIFY_FILE_DIFF,
            SOME_MODIFY_FILE_DIFF,
        ),
        (
            _delete_existing_file,
            [SOME_CONTENT_FILENAME],
            _delete_existing_file,
            [SOME_CONTENT_FILENAME],
            SOME_DELETE_FILE_DIFF,
            SOME_DELETE_FILE_DIFF,
        ),
        (
            _add_new_file,
            [SOME_OTHER_FILENAME],
            _add_new_file,
            [SOME_OTHER_FILENAME],
            SOME_NEW_FILE_DIFF,
            SOME_NEW_FILE_DIFF,
        ),
        (
            _modify_existing_file,
            [SOME_CONTENT_FILENAME, SOME_CONTENT],
            _add_new_file,
            [SOME_OTHER_FILENAME],
            SOME_MODIFY_FILE_DIFF,
            SOME_NEW_FILE_DIFF,
        ),
        (
            _delete_existing_file,
            [SOME_CONTENT_FILENAME],
            _modify_existing_file,
            [SOME_CONTENT_FILENAME, SOME_CONTENT],
            SOME_DELETE_FILE_DIFF,
            SOME_MODIFY_FILE_DIFF,
        ),
        (
            _add_new_file,
            [SOME_OTHER_FILENAME],
            _delete_existing_file,
            [SOME_CONTENT_FILENAME],
            SOME_NEW_FILE_DIFF,
            SOME_DELETE_FILE_DIFF,
        ),
    ],
)
def test_feature_branch_context_manager__add_new_file_in_different_branches__clean_up_successfully(
    tmp_path,
    some_source_modifier,
    some_source_modifier_inputs,
    some_other_source_modifier,
    some_other_source_modifier_inputs,
    some_result,
    some_other_result,
):
    local_repo = _initialize_multiple_empty_repos(tmp_path).local_repo
    some_branch_name = SOME_BRANCH_NAME
    with feature_branch(local_repo, some_branch_name):
        some_source_modifier(local_repo, *some_source_modifier_inputs)
        some_diff = _get_diff(local_repo)
        assert some_diff == some_result
    some_other_branch_name = SOME_OTHER_BRANCH_NAME
    with feature_branch(local_repo, some_other_branch_name):
        some_other_source_modifier(local_repo, *some_other_source_modifier_inputs)
        some_other_diff = _get_diff(local_repo)
        assert some_other_diff == some_other_result


    new_file_path = remote_path / SOME_CONTENT_FILENAME
    new_file_path.write_text(SOME_CHANGES)


def _get_diff(repo: Repo) -> str:
    """
    Helper function used to handle the logic of generating diff text via a feature branch.

    This diff will only reflect the changes since the last commit.
    This includes staging the local changes.
    """

    index = repo.index
    workdir_path = Path(repo.working_dir)

    untracked_file_paths = [Path(f) for f in repo.untracked_files]
    items_to_stage = untracked_file_paths + [Path(f.a_path) for f in index.diff(None)]

    for item in items_to_stage:
        full_path = workdir_path / item
        index.add(str(item)) if full_path.exists() else index.remove(str(item), r=True)

    return repo.git.diff("--cached")