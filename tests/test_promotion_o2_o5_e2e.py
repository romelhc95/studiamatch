import subprocess

from scripts.security.validate_work_package import validate_git_promotion_dag


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


def promotion_candidate_and_merge(repo, target, source, branch):
    git(repo, "switch", target)
    target_sha = git(repo, "rev-parse", "HEAD")
    source_sha = git(repo, "rev-parse", source)
    git(repo, "switch", "-c", branch, target_sha)
    git(repo, "merge", "--no-ff", "--no-edit", source)
    candidate_sha = git(repo, "rev-parse", "HEAD")
    assert git(repo, "show", "-s", "--format=%P", candidate_sha).split() == [target_sha, source_sha]
    git(repo, "switch", target)
    git(repo, "merge", "--no-ff", "--no-edit", branch)
    merge_sha = git(repo, "rev-parse", "HEAD")
    return {"target_sha": target_sha, "source_sha": source_sha, "candidate_sha": candidate_sha, "merge_sha": merge_sha}


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
    o2 = promotion_candidate_and_merge(repo, "certificacion", "desarrollo", "promote-o2")
    o2["name"] = "O2"
    o3 = promotion_candidate_and_merge(repo, "main", "certificacion", "promote-o3")
    o3["name"] = "O3"
    o4 = promotion_candidate_and_merge(repo, "certificacion", "main", "promote-o4")
    o4["name"] = "O4"
    o5 = promotion_candidate_and_merge(repo, "desarrollo", "certificacion", "promote-o5")
    o5["name"] = "O5"
    assert_chain_closed(repo)
    assert validate_git_promotion_dag(repo, [o2, o3, o4, o5]) == []


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
    o2 = promotion_candidate_and_merge(repo, "certificacion", "desarrollo", "promote-o2")
    o2["name"] = "O2"
    o3 = promotion_candidate_and_merge(repo, "main", "certificacion", "promote-o3")
    o3["name"] = "O3"
    o3_merge = o3["merge_sha"]
    drift = commit_file(repo, "drift.txt", "interleaved\n")
    assert int(git(repo, "rev-list", "--count", f"{o3_merge}..{drift}")) == 1
    o4 = promotion_candidate_and_merge(repo, "certificacion", "main", "promote-o4")
    o4["name"] = "O4"
    o5 = promotion_candidate_and_merge(repo, "desarrollo", "certificacion", "promote-o5")
    o5["name"] = "O5"
    errors = validate_git_promotion_dag(repo, [o2, o3, o4, o5])
    assert "DAG_O4_TREE_MISMATCH" in errors or "DAG_O4_FINAL_TREE_DRIFT" in errors


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
    stage = {"name": "O2", "target_sha": target, "source_sha": source, "candidate_sha": git(repo, "rev-parse", "HEAD"), "merge_sha": git(repo, "rev-parse", "HEAD")}
    assert "DAG_O2_CANDIDATE_PARENTS_INVALID" in validate_git_promotion_dag(repo, [stage])
