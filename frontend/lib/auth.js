import { auth, db, googleProvider } from "./firebase";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  updateProfile,
} from "firebase/auth";
import { doc, setDoc, getDoc, serverTimestamp } from "firebase/firestore";

const USER_COLLECTION = "users";

function userDocRef(uid) {
  return doc(db, USER_COLLECTION, uid);
}

export async function saveUserProfile(uid, profile) {
  const ref = userDocRef(uid);
  const existing = await getDoc(ref);
  const base = {
    updatedAt: serverTimestamp(),
  };
  if (!existing.exists()) {
    await setDoc(ref, { ...profile, createdAt: serverTimestamp(), ...base });
  } else {
    await setDoc(ref, { ...existing.data(), ...profile, ...base });
  }
  const finalSnap = await getDoc(ref);
  return finalSnap.data();
}

export async function signUpEmailPassword({
  name,
  email,
  password,
  org,
  role,
  industry,
}) {
  const cred = await createUserWithEmailAndPassword(auth, email, password);
  if (name) {
    await updateProfile(cred.user, { displayName: name });
  }
  const profile = await saveUserProfile(cred.user.uid, {
    name: name || cred.user.displayName || "",
    email,
    org: org || "",
    role: role || "",
    industry: industry || "",
    provider: "password",
  });
  return { uid: cred.user.uid, ...profile };
}

export async function signInEmailPassword({ email, password }) {
  const cred = await signInWithEmailAndPassword(auth, email, password);
  const snap = await getDoc(userDocRef(cred.user.uid));
  return {
    uid: cred.user.uid,
    email: cred.user.email,
    name: cred.user.displayName || "",
    ...(snap.exists() ? snap.data() : {}),
  };
}

export async function signInWithGoogleInteractive(extraFields) {
  const result = await signInWithPopup(auth, googleProvider);
  const u = result.user;
  // If first time (no doc) require extra fields (org, role, industry) provided by caller
  const snap = await getDoc(userDocRef(u.uid));
  let profileUpdate = {};
  if (!snap.exists()) {
    profileUpdate = {
      name: u.displayName || "",
      email: u.email || "",
      photoURL: u.photoURL || "",
      org: extraFields?.org || "",
      role: extraFields?.role || "",
      industry: extraFields?.industry || "",
      provider: "google",
    };
  } else {
    profileUpdate = {
      provider: "google",
      photoURL: u.photoURL || snap.data().photoURL || "",
    };
  }
  const profile = await saveUserProfile(u.uid, profileUpdate);
  return { uid: u.uid, ...profile };
}

// New flow: first do bare Google sign-in; if user doc absent, caller must collect extra fields then call saveUserProfile.
export async function signInWithGoogleRaw() {
  const result = await signInWithPopup(auth, googleProvider);
  const u = result.user;
  const snap = await getDoc(userDocRef(u.uid));
  const isNew = !snap.exists();
  return {
    isNewUser: isNew,
    authUser: {
      uid: u.uid,
      email: u.email || "",
      name: u.displayName || "",
      photoURL: u.photoURL || "",
      provider: "google",
    },
    existingProfile: isNew ? null : snap.data(),
  };
}
