import { NextResponse } from "next/server";
import { Storage } from "@google-cloud/storage";

// Defensive: ensure this route isn't executed in edge runtime where native deps might break.
export const runtime = 'nodejs';

let storage; // lazy init to surface credential errors once
function getStorage() {
  if (!storage) {
    const keyFile = process.env.GOOGLE_APPLICATION_CREDENTIALS;
    if (!keyFile) throw new Error("GOOGLE_APPLICATION_CREDENTIALS not set");
    storage = new Storage({ keyFilename: keyFile });
  }
  return storage;
}

export async function POST(req) {
  const bucketName = process.env.GCS_BUCKET_NAME;
  if (!bucketName) {
    return NextResponse.json(
      { error: "Server misconfiguration: GCS_BUCKET_NAME missing" },
      { status: 500 }
    );
  }
  try {
    const formData = await req.formData();
    const file = formData.get("file");
    if (!file) {
      return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
    }
    // Some environments provide file as a Blob without name/type fallback
    const originalName = file.name || 'dataset.json';
    const contentType = file.type || 'application/json';

    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    if (buffer.length === 0) {
      return NextResponse.json({ error: "Empty file" }, { status: 400 });
    }

    const safeBase = originalName.replace(/[^a-zA-Z0-9._-]/g, '_');
    const fileName = `${Date.now()}-${safeBase}`;

    const gcs = getStorage();
    const bucket = gcs.bucket(bucketName);
    const blob = bucket.file(fileName);

    await blob.save(buffer, {
      metadata: { contentType },
      resumable: false,
      validation: 'crc32c'
    });

    // Optionally make public – consider restricting later
    try {
      await blob.makePublic();
    } catch (e) {
      console.warn("makePublic failed (non-fatal)", e.message);
    }

    const publicUrl = `https://storage.googleapis.com/${bucketName}/${encodeURIComponent(fileName)}`;
    return NextResponse.json({ success: true, url: publicUrl, name: fileName });
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json(
      { error: error.message || "Upload failed" },
      { status: 500 }
    );
  }
}
