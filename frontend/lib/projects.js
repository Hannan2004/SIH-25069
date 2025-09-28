import { db } from "./firebase";
import {
  collection,
  addDoc,
  serverTimestamp,
  getDoc,
  doc,
  updateDoc,
  setDoc,
  query,
  getDocs,
  where,
} from "firebase/firestore";

const PROJECTS = "projects";

export async function createProject(data, user) {
  const col = collection(db, PROJECTS);
  const docRef = await addDoc(col, {
    ...data,
    ownerUid: user?.uid || null,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  });
  return docRef.id;
}

export async function getProject(id) {
  const snap = await getDoc(doc(db, PROJECTS, id));
  if (!snap.exists()) return null;
  return { id: snap.id, ...snap.data() };
}

export async function updateProject(id, partial) {
  await updateDoc(doc(db, PROJECTS, id), {
    ...partial,
    updatedAt: serverTimestamp(),
  });
}

// Datasets subcollection helpers
// Path: projects/{projectId}/datasets/{datasetId}
export async function addDataset(projectId, data) {
  const col = collection(db, PROJECTS, projectId, "datasets");
  const ref = await addDoc(col, {
    ...data,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  });
  return ref.id;
}

export async function setDataset(projectId, datasetId, data) {
  await setDoc(
    doc(db, PROJECTS, projectId, "datasets", datasetId),
    {
      ...data,
      updatedAt: serverTimestamp(),
    },
    { merge: true }
  );
}

export async function listDatasets(projectId) {
  const q = query(collection(db, PROJECTS, projectId, "datasets"));
  const snap = await getDocs(q);
  return snap.docs.map((d) => ({ id: d.id, ...d.data() }));
}

export async function getDataset(projectId, datasetId) {
  const snap = await getDoc(
    doc(db, PROJECTS, projectId, "datasets", datasetId)
  );
  if (!snap.exists()) return null;
  return { id: snap.id, ...snap.data() };
}

// Analyses subcollection helpers
// Path: projects/{projectId}/analyses/{analysisId}
export async function addAnalysis(projectId, data) {
  const col = collection(db, PROJECTS, projectId, "analyses");
  const ref = await addDoc(col, {
    ...data,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  });
  return ref.id;
}

export async function getAnalysis(projectId, analysisId) {
  const snap = await getDoc(
    doc(db, PROJECTS, projectId, "analyses", analysisId)
  );
  if (!snap.exists()) return null;
  return { id: snap.id, ...snap.data() };
}

export async function listAnalyses(projectId) {
  const q = query(collection(db, PROJECTS, projectId, "analyses"));
  const snap = await getDocs(q);
  return snap.docs.map((d) => ({ id: d.id, ...d.data() }));
}

// List projects (optionally by owner)
export async function listProjects(ownerUid) {
  let qRef;
  if (ownerUid) {
    qRef = query(collection(db, PROJECTS), where("ownerUid", "==", ownerUid));
  } else {
    qRef = query(collection(db, PROJECTS));
  }
  const snap = await getDocs(qRef);
  return snap.docs.map((d) => ({ id: d.id, ...d.data() }));
}
