import { NextResponse } from "next/server";
import { Storage } from "@google-cloud/storage";
import path from "path";
import fs from "fs/promises";

// Initialize Google Cloud Storage client
const storage = new Storage({
  keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS,
});

const bucketName = process.env.GCS_BUCKET_NAME;

export async function POST(req) {
  try {
    // Parse incoming file
    const formData = await req.formData();
    const file = formData.get("file"); // <input name="file" />
    if (!file) {
      return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
    }

    // Convert file to buffer
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // Create a unique file name
    const fileName = `${Date.now()}-${file.name}`;
    const bucket = storage.bucket(bucketName);
    const blob = bucket.file(fileName);

    // Upload file
    await blob.save(buffer, {
      metadata: { contentType: file.type },
      resumable: false,
    });

    // Make file public (optional for testing)
    await blob.makePublic();

    // Public URL
    const publicUrl = `https://storage.googleapis.com/${bucketName}/${fileName}`;
    console.log("Uploaded file URL:", publicUrl);

    return NextResponse.json({ success: true, url: publicUrl });
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}
