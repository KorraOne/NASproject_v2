import { useCallback, useEffect, useMemo, useState } from "react";

import { Link } from "react-router-dom";

import { listArchetypes, replaceArchetypePermissions } from "../api/archetypes";

import {

  getFolderArchetypePermissions,

  listFolders,

  replaceFolderArchetypePermissions,

} from "../api/folders";

import { listEffectivePermissions } from "../api/permissions";

import { ApiRequestError } from "../api/client";

import { useToast } from "../components/Toast";

import {

  ArchetypeFolderMatrix,

  archetypeMapToPayload,

  buildArchetypePermissionMap,

  type ArchetypePermissionMap,

} from "../components/ArchetypeFolderMatrix";

import {

  buildFolderArchetypePermissionMap,

  folderArchetypeMapToPayload,

  FolderArchetypeMatrix,

  type FolderArchetypePermissionMap,

} from "../components/FolderArchetypeMatrix";

import { ErrorBanner } from "../components/ErrorBanner";

import { Loading } from "../components/Loading";

import { PageIntro } from "../components/PageIntro";

import { permissionLabel } from "../permissions";

import type { Archetype, EffectivePermission, SharedFolder } from "../types";



type Tab = "archetype" | "folder" | "user";



export function PermissionsPage() {

  const { showToast } = useToast();

  const [tab, setTab] = useState<Tab>("archetype");

  const [archetypes, setArchetypes] = useState<Archetype[]>([]);

  const [folders, setFolders] = useState<SharedFolder[]>([]);

  const [effective, setEffective] = useState<EffectivePermission[]>([]);

  const [selectedArchetypeId, setSelectedArchetypeId] = useState<number | "">("");

  const [selectedFolderId, setSelectedFolderId] = useState<number | "">("");

  const [matrix, setMatrix] = useState<ArchetypePermissionMap>({});

  const [savedMatrix, setSavedMatrix] = useState<ArchetypePermissionMap>({});

  const [folderMatrix, setFolderMatrix] = useState<FolderArchetypePermissionMap>({});

  const [savedFolderMatrix, setSavedFolderMatrix] = useState<FolderArchetypePermissionMap>({});

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const [busy, setBusy] = useState(false);



  const selectedArchetype = archetypes.find((a) => a.id === selectedArchetypeId) ?? null;



  const archetypeDirty = useMemo(

    () => JSON.stringify(matrix) !== JSON.stringify(savedMatrix),

    [matrix, savedMatrix],

  );



  const folderDirty = useMemo(

    () => JSON.stringify(folderMatrix) !== JSON.stringify(savedFolderMatrix),

    [folderMatrix, savedFolderMatrix],

  );



  const load = useCallback(async () => {

    setLoading(true);

    setError(null);

    try {

      const [archetypeList, folderList, effectiveList] = await Promise.all([

        listArchetypes(),

        listFolders(),

        listEffectivePermissions(),

      ]);

      setArchetypes(archetypeList);

      setFolders(folderList);

      setEffective(effectiveList);

      const initialArchetypeId = archetypeList[0]?.id ?? "";

      setSelectedArchetypeId(initialArchetypeId);

      const archetype = archetypeList[0];

      if (archetype) {

        const map = buildArchetypePermissionMap(folderList, archetype.folder_permissions);

        setMatrix(map);

        setSavedMatrix(map);

      }

      if (folderList.length > 0) {
        const initialFolderId = folderList[0].id;
        setSelectedFolderId(initialFolderId);
        const perms = await getFolderArchetypePermissions(initialFolderId);

        const fMap = buildFolderArchetypePermissionMap(

          archetypeList,

          perms.map((p) => ({ archetype_id: p.archetype_id, access: p.access })),

        );

        setFolderMatrix(fMap);

        setSavedFolderMatrix(fMap);
      }

    } catch (err) {

      setError(err instanceof ApiRequestError ? err.message : "Could not load permissions.");

    } finally {

      setLoading(false);

    }

  }, []);



  useEffect(() => {

    load();

  }, [load]);



  function onSelectArchetype(id: number) {

    setSelectedArchetypeId(id);

    const archetype = archetypes.find((a) => a.id === id);

    if (!archetype) return;

    const map = buildArchetypePermissionMap(folders, archetype.folder_permissions);

    setMatrix(map);

    setSavedMatrix(map);

  }



  async function onSelectFolder(id: number) {

    setSelectedFolderId(id);

    try {

      const perms = await getFolderArchetypePermissions(id);

      const fMap = buildFolderArchetypePermissionMap(

        archetypes,

        perms.map((p) => ({ archetype_id: p.archetype_id, access: p.access })),

      );

      setFolderMatrix(fMap);

      setSavedFolderMatrix(fMap);

    } catch (err) {

      setError(err instanceof ApiRequestError ? err.message : "Could not load folder permissions.");

    }

  }



  async function onSaveArchetype() {

    if (selectedArchetypeId === "") return;

    setBusy(true);

    setError(null);

    try {

      await replaceArchetypePermissions(

        Number(selectedArchetypeId),

        archetypeMapToPayload(matrix),

      );

      await load();

      showToast("Permissions saved.");

    } catch (err) {

      setError(err instanceof ApiRequestError ? err.message : "Could not save permissions.");

    } finally {

      setBusy(false);

    }

  }



  async function onSaveFolder() {

    if (selectedFolderId === "") return;

    setBusy(true);

    setError(null);

    try {

      await replaceFolderArchetypePermissions(

        Number(selectedFolderId),

        folderArchetypeMapToPayload(folderMatrix),

      );

      await load();

      showToast("Permissions saved.");

    } catch (err) {

      setError(err instanceof ApiRequestError ? err.message : "Could not save permissions.");

    } finally {

      setBusy(false);

    }

  }



  if (loading) return <Loading label="Loading permissions…" />;



  const saveAction =

    tab === "archetype" ? (

      <button

        type="button"

        className="btn btn-primary"

        disabled={busy || !archetypeDirty || selectedArchetypeId === ""}

        onClick={onSaveArchetype}

      >

        {busy ? "Saving…" : archetypeDirty ? "Save changes" : "Saved"}

      </button>

    ) : tab === "folder" ? (

      <button

        type="button"

        className="btn btn-primary"

        disabled={busy || !folderDirty || selectedFolderId === ""}

        onClick={onSaveFolder}

      >

        {busy ? "Saving…" : folderDirty ? "Save changes" : "Saved"}

      </button>

    ) : null;



  return (

    <div className="page">

      <PageIntro

        title="Permissions"

        lede="Control shared folder access by archetype or folder. See effective access per person on the By user tab."

        action={saveAction}

      />

      <ErrorBanner message={error} />



      <div className="permissions-tabs" role="tablist" aria-label="Permission views">

        <button

          type="button"

          role="tab"

          className={tab === "archetype" ? "active" : undefined}

          aria-selected={tab === "archetype"}

          onClick={() => setTab("archetype")}

        >

          By archetype

        </button>

        <button

          type="button"

          role="tab"

          className={tab === "folder" ? "active" : undefined}

          aria-selected={tab === "folder"}

          onClick={() => setTab("folder")}

        >

          By folder

        </button>

        <button

          type="button"

          role="tab"

          className={tab === "user" ? "active" : undefined}

          aria-selected={tab === "user"}

          onClick={() => setTab("user")}

        >

          By user

        </button>

      </div>



      {tab === "archetype" ? (

        <section className="card section-card">

          <label>

            Archetype

            <select

              value={selectedArchetypeId}

              onChange={(e) => onSelectArchetype(Number(e.target.value))}

            >

              {archetypes.map((archetype) => (

                <option key={archetype.id} value={archetype.id}>

                  {archetype.name}

                </option>

              ))}

            </select>

          </label>

          {selectedArchetype?.can_view_all_personal ? (

            <p className="hint section-card-lede">

              Super User can view all personal folders. Shared folder access below is optional.

            </p>

          ) : null}

          <ArchetypeFolderMatrix folders={folders} value={matrix} onChange={setMatrix} />

          <p className="hint">

            Changes apply to everyone assigned this archetype.{" "}

            <Link to="/users/archetypes">Manage archetypes</Link>

          </p>

        </section>

      ) : tab === "folder" ? (

        <section className="card section-card">

          {folders.length === 0 ? (

            <p className="muted">

              Add a <Link to="/folders/new">shared folder</Link> first.

            </p>

          ) : (

            <>

              <label>

                Shared folder

                <select

                  value={selectedFolderId}

                  onChange={(e) => onSelectFolder(Number(e.target.value))}

                >

                  {folders.map((folder) => (

                    <option key={folder.id} value={folder.id}>

                      {folder.name}

                    </option>

                  ))}

                </select>

              </label>

              <p className="hint section-card-lede">

                Set which archetypes can access this folder. Same data as the By archetype tab.

              </p>

              <FolderArchetypeMatrix

                archetypes={archetypes}

                value={folderMatrix}

                onChange={setFolderMatrix}

              />

            </>

          )}

        </section>

      ) : (

        <section className="card section-card">

          {effective.length === 0 ? (

            <p className="muted">Add file users to see effective permissions.</p>

          ) : (

            <table className="data-table effective-permissions-table">

              <thead>

                <tr>

                  <th>Person</th>

                  <th>Archetype</th>

                  <th>Personal folder</th>

                  <th>Shared folders</th>

                </tr>

              </thead>

              <tbody>

                {effective.map((row) => (

                  <tr key={row.user_id}>

                    <td>

                      <strong>{row.display_name}</strong>

                      <br />

                      <code>{row.username}</code>

                    </td>

                    <td>

                      {row.archetype_name ?? "—"}

                      {row.can_view_all_personal ? (

                        <>

                          <br />

                          <span className="effective-badge">All personal folders</span>

                        </>

                      ) : null}

                      {row.elevation ? (

                        <>

                          <br />

                          <span className="effective-badge">Temporary access</span>

                          <br />

                          <Link to={`/users/${row.user_id}/temporary-access`}>Manage</Link>

                          <ul className="elevation-grant-list">

                            {row.elevation.grants.map((grant) => (

                              <li key={`${grant.grant_type}-${grant.target_id}`}>

                                {grant.target_name}: {permissionLabel(grant.access)}

                              </li>

                            ))}

                          </ul>

                        </>

                      ) : null}

                    </td>

                    <td>

                      <code>W:\{row.personal_folder}</code>

                    </td>

                    <td>

                      {row.shared_folders.length === 0 ? (

                        <span className="muted">None</span>

                      ) : (

                        <ul>

                          {row.shared_folders.map((folder) => (

                            <li key={folder.folder_name}>

                              {folder.folder_name}: {permissionLabel(folder.access)}

                            </li>

                          ))}

                        </ul>

                      )}

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          )}

        </section>

      )}

    </div>

  );

}

