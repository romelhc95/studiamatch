import subprocess


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def commit_file(repo, name, text):
    (repo / name).write_text(text, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-m", f"commit {name}")
    return git(repo, "rev-parse", "HEAD")


def merge_no_ff(repo, target, source):
    git(repo, "switch", target)
    before = git(repo, "rev-parse", "HEAD")
    source_sha = git(repo, "rev-parse", source)
    git(repo, "merge", "--no-ff", "--no-edit", source)
    merge = git(repo, "rev-parse", "HEAD")
    parents = git(repo, "show", "-s", "--format=%P", merge).split()
    assert parents == [before, source_sha]
    assert git(repo, "rev-parse", f"{merge}^{{tree}}") == git(repo, "rev-parse", f"{source_sha}^{{tree}}")
    return merge


def assert_chain_closed(repo):
    trees = {git(repo, "rev-parse", f"{ref}^{{tree}}") for ref in ("main", "certificacion", "desarrollo")}
    assert len(trees) == 1
    assert subprocess.run(["git", "merge-base", "--is-ancestor", "main", "certificacion"], cwd=repo).returncode == 0
    assert subprocess.run(["git", "merge-base", "--is-ancestor", "certificacion", "desarrollo"], cwd=repo).returncode == 0


def test_real_git_o2_o5_chain(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    commit_file(repo, "state.txt", "base\n")
    git(repo, "switch", "-c", "desarrollo")
    commit_file(repo, "state.txt", "hom012\n")
    git(repo, "switch", "main")
    git(repo, "switch", "-c", "certificacion")
    o2 = merge_no_ff(repo, "certificacion", "desarrollo")
    o3 = merge_no_ff(repo, "main", "certificacion")
    o4 = merge_no_ff(repo, "certificacion", "main")
    o5 = merge_no_ff(repo, "desarrollo", "certificacion")
    assert_chain_closed(repo)
    assert len({o2, o3, o4, o5}) == 4


def test_real_git_o2_o5_rejects_interleaved_commit(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    commit_file(repo, "state.txt", "base\n")
    git(repo, "switch", "-c", "desarrollo")
    commit_file(repo, "state.txt", "hom012\n")
    git(repo, "switch", "main")
    git(repo, "switch", "-c", "certificacion")
    merge_no_ff(repo, "certificacion", "desarrollo")
    o3 = merge_no_ff(repo, "main", "certificacion")
    drift = commit_file(repo, "drift.txt", "interleaved\n")
    assert int(git(repo, "rev-list", "--count", f"{o3}..{drift}")) == 1
    merge_no_ff(repo, "certificacion", "main")
    merge_no_ff(repo, "desarrollo", "certificacion")
    assert "drift.txt" in git(repo, "diff", "--name-only", o3, "main")


def test_real_git_candidate_rejects_wrong_parent_order(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    base = commit_file(repo, "state.txt", "base\n")
    git(repo, "switch", "-c", "desarrollo")
    source = commit_file(repo, "state.txt", "hom012\n")
    git(repo, "switch", "main")
    target = commit_file(repo, "target.txt", "target drift\n")
    git(repo, "switch", "desarrollo")
    git(repo, "switch", "-c", "candidate")
    git(repo, "merge", "--no-ff", "--no-edit", "main")
    parents = git(repo, "show", "-s", "--format=%P", "HEAD").split()
    assert parents == [source, target]
    assert parents != [target, source]
