<script>
  // Loads boards from server
  export let data;
</script>

<div class="board-bg">
  <h1>Boards</h1>
  <div class="board-list">
    {#if data?.boards?.length}
      {#each data.boards as board}
        <a class="board-card" href="/tasks/board/{board.id}">
          <div class="board-title">{board.name}</div>
        </a>
      {/each}
    {:else}
      <p class="no-boards">No boards found.</p>
    {/if}
    <form class="board-card board-create" method="POST" action="?/create">
      <div class="plus-icon">+</div>
      <label for="board-name" class="sr-only">Board name</label>
      <input id="board-name" name="name" placeholder="New board name" required />
      <button type="submit">Create Board</button>
    </form>
  </div>
</div>

<style>

.board-bg {
  padding: 2.5rem 0 2rem 0;
  min-height: 100vh;
}
h1 {
  color: #253858;
  font-size: 2.2rem;
  font-weight: 800;
  margin-bottom: 1.5rem;
  letter-spacing: -1px;
}
.board-list {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  margin-top: 2rem;
}
.board-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  background: #f4f5f7;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(9,30,66,.13);
  padding: 1.7rem 2.2rem 1.2rem 2.2rem;
  min-width: 240px;
  min-height: 120px;
  text-decoration: none;
  color: #172b4d;
  font-size: 1.2rem;
  font-weight: 600;
  transition: box-shadow 0.18s, background 0.18s, transform 0.12s;
  cursor: pointer;
  position: relative;
}
.board-card:hover {
  background: #e4e6ea;
  box-shadow: 0 6px 24px 0 rgba(9,30,66,.18);
  transform: translateY(-3px) scale(1.03);
}
.board-title {
  margin-bottom: 0.5rem;
  font-size: 1.35rem;
  font-weight: bold;
  letter-spacing: -0.5px;
}
.board-create {
  background: #fff;
  border: 2px dashed #b6bac2;
  color: #5e6c84;
  align-items: center;
  min-height: 120px;
  justify-content: center;
  box-shadow: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  position: relative;
}
.board-create:hover {
  border-color: #0079bf;
  box-shadow: 0 2px 12px 0 rgba(9,30,66,.10);
}
.board-create input {
  border: none;
  background: transparent;
  font-size: 1.08rem;
  margin-bottom: 0.5rem;
  outline: none;
  width: 100%;
  color: #253858;
  padding: 0.2rem 0.1rem;
  border-bottom: 1.5px solid #e4e6ea;
  transition: border-color 0.15s;
}
.board-create input:focus {
  border-bottom: 1.5px solid #0079bf;
}
.board-create button {
  background: #0079bf;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1.1rem;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 0.5rem;
  font-weight: 600;
  transition: background 0.15s;
  box-shadow: 0 1px 4px 0 rgba(9,30,66,.10);
}
.board-create button:hover {
  background: #026aa7;
}
.plus-icon {
  font-size: 2.2rem;
  color: #b6bac2;
  margin-bottom: 0.3rem;
  font-weight: 700;
  align-self: center;
}
.no-boards {
  color: #7a869a;
  font-size: 1.1rem;
  margin-top: 1.5rem;
}
</style>
